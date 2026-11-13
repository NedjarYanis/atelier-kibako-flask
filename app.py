from datetime import datetime, timezone
from decimal import Decimal
import re
import uuid

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import inspect, text

from config_manager import (
    DEFAULT_SQLITE_URI,
    build_mariadb_uri,
    ensure_database_exists,
    load_env_config,
    mask_uri,
    normalize_db_uri,
    save_env_config,
    test_database_connection,
)
from models import Category, Order, OrderItem, Product, db, seed_catalog

FREE_SHIPPING_THRESHOLD = Decimal("80.00")
STANDARD_SHIPPING_COST = Decimal("6.90")
ORDER_STATUSES = ["En attente", "En préparation", "Expédiée", "Livrée", "Annulée"]


def _slugify(text_val: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (text_val or "").lower()).strip("-")
    return slug or f"kibako-{uuid.uuid4().hex[:6]}"


def create_app() -> Flask:
    app = Flask(__name__)
    cfg = load_env_config()

    app.config["SECRET_KEY"] = cfg["secret_key"]
    app.config["SQLALCHEMY_DATABASE_URI"] = cfg["database_uri"]
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    app.config["DB_CONFIGURED"] = cfg["configured"]
    app.config["DB_MODE"] = cfg["db_mode"]

    db.init_app(app)

    def check_db_ready() -> tuple[bool, str | None]:
        """Vérifie sans planter si la base est joignable et si les tables existent."""
        try:
            with app.app_context():
                db.session.execute(text("SELECT 1"))
                inspector = inspect(db.engine)
                has_tables = inspector.has_table("products") and inspector.has_table("categories")
                if not has_tables:
                    return False, "Tables ORM non initialisées. Rendez-vous sur /setup pour initialiser le catalogue."
                return True, None
        except Exception as exc:
            return False, f"Base de données non connectée : {exc}"

    def hot_swap_engine(new_uri: str, db_mode: str) -> None:
        """Bascule le moteur SQLAlchemy à chaud sans redémarrer Flask."""
        with app.app_context():
            db.session.remove()
            try:
                for eng in db.engines.values():
                    eng.dispose()
            except Exception:
                pass

            app.config["SQLALCHEMY_DATABASE_URI"] = new_uri
            app.config["DB_CONFIGURED"] = True
            app.config["DB_MODE"] = db_mode

            options = dict(app.config.get("SQLALCHEMY_ENGINE_OPTIONS") or {})
            options["url"] = new_uri
            new_engine = db._make_engine(None, options, app)
            db._app_engines.setdefault(app, {})[None] = new_engine

            db.create_all()

    # Initialisation douce au démarrage : ne plante jamais si MariaDB est absent
    with app.app_context():
        if cfg["configured"]:
            try:
                db.session.execute(text("SELECT 1"))
            except Exception:
                pass
        else:
            # Prépare l'aperçu SQLite local sans bloquer /setup
            try:
                ensure_database_exists(DEFAULT_SQLITE_URI)
                db.create_all()
            except Exception:
                pass

    @app.context_processor
    def inject_globals():
        cart = session.get("cart", {})
        cart_count = sum(int(qty) for qty in cart.values()) if isinstance(cart, dict) else 0
        db_ok, db_msg = check_db_ready()
        categories_nav = []
        if db_ok:
            try:
                categories_nav = Category.query.order_by(Category.name.asc()).all()
            except Exception:
                categories_nav = []
        return {
            "cart_count": cart_count,
            "db_status": {
                "ready": db_ok,
                "message": db_msg,
                "configured": app.config.get("DB_CONFIGURED", False),
                "mode": app.config.get("DB_MODE", "unconfigured"),
                "masked_uri": mask_uri(app.config.get("SQLALCHEMY_DATABASE_URI", "")),
            },
            "categories_nav": categories_nav,
            "free_shipping_threshold": FREE_SHIPPING_THRESHOLD,
        }

    # ------------------------------------------------------------------
    # Pages Boutique
    # ------------------------------------------------------------------
    @app.route("/")
    def index():
        db_ok, _ = check_db_ready()
        featured_products = []
        categories = []
        if db_ok:
            featured_products = (
                Product.query.filter_by(featured=True)
                .order_by(Product.created_at.desc())
                .limit(4)
                .all()
            )
            categories = Category.query.order_by(Category.id.asc()).all()
        return render_template(
            "index.html",
            featured_products=featured_products,
            categories=categories,
        )

    @app.route("/catalogue")
    def catalogue():
        db_ok, _ = check_db_ready()
        if not db_ok:
            return render_template(
                "catalogue.html",
                products=[],
                categories=[],
                universes=[],
                woods=[],
                mechanisms=[],
                filters={},
            )

        q = request.args.get("q", "").strip()
        cat_slug = request.args.get("category", "").strip()
        universe = request.args.get("universe", "").strip()
        wood = request.args.get("wood", "").strip()
        mechanism = request.args.get("mechanism", "").strip()
        sort = request.args.get("sort", "featured").strip()

        query = Product.query
        if q:
            like = f"%{q}%"
            query = query.filter(
                db.or_(
                    Product.name.ilike(like),
                    Product.universe.ilike(like),
                    Product.melody_title.ilike(like),
                    Product.wood_type.ilike(like),
                )
            )
        if cat_slug:
            query = query.join(Category).filter(Category.slug == cat_slug)
        if universe:
            query = query.filter(Product.universe == universe)
        if wood:
            query = query.filter(Product.wood_type == wood)
        if mechanism:
            query = query.filter(Product.mechanism == mechanism)

        if sort == "price_asc":
            query = query.order_by(Product.price.asc())
        elif sort == "price_desc":
            query = query.order_by(Product.price.desc())
        elif sort == "newest":
            query = query.order_by(Product.created_at.desc())
        else:
            query = query.order_by(Product.featured.desc(), Product.id.asc())

        products = query.all()
        categories = Category.query.order_by(Category.name.asc()).all()
        universes = [r[0] for r in db.session.query(Product.universe).distinct().order_by(Product.universe).all()]
        woods = [r[0] for r in db.session.query(Product.wood_type).distinct().order_by(Product.wood_type).all()]
        mechanisms = [r[0] for r in db.session.query(Product.mechanism).distinct().order_by(Product.mechanism).all()]

        return render_template(
            "catalogue.html",
            products=products,
            categories=categories,
            universes=universes,
            woods=woods,
            mechanisms=mechanisms,
            filters={
                "q": q,
                "category": cat_slug,
                "universe": universe,
                "wood": wood,
                "mechanism": mechanism,
                "sort": sort,
            },
        )

    @app.route("/produit/<slug>")
    def product_detail(slug: str):
        db_ok, _ = check_db_ready()
        if not db_ok:
            flash("Veuillez initialiser la base de données via /setup.", "warning")
            return redirect(url_for("setup_page"))

        product = Product.query.filter_by(slug=slug).first_or_404()
        related = (
            Product.query.filter(Product.category_id == product.category_id, Product.id != product.id)
            .limit(3)
            .all()
        )
        return render_template("product.html", product=product, related=related)

    # ------------------------------------------------------------------
    # Panier & Commande (Session + Transaction ORM)
    # ------------------------------------------------------------------
    def _build_cart_summary():
        cart = session.get("cart", {})
        items = []
        subtotal = Decimal("0.00")
        db_ok, _ = check_db_ready()
        if not db_ok or not isinstance(cart, dict):
            return items, subtotal, Decimal("0.00"), Decimal("0.00")

        for pid_str, qty in list(cart.items()):
            try:
                pid = int(pid_str)
                qty_int = max(1, int(qty))
            except (TypeError, ValueError):
                continue
            product = db.session.get(Product, pid)
            if not product:
                continue
            line_total = Decimal(str(product.price)) * qty_int
            subtotal += line_total
            items.append(
                {
                    "product": product,
                    "quantity": qty_int,
                    "line_total": line_total,
                }
            )

        if not items:
            shipping = Decimal("0.00")
        elif subtotal >= FREE_SHIPPING_THRESHOLD:
            shipping = Decimal("0.00")
        else:
            shipping = STANDARD_SHIPPING_COST

        total = subtotal + shipping
        return items, subtotal, shipping, total

    @app.route("/panier")
    def cart_view():
        items, subtotal, shipping, total = _build_cart_summary()
        remaining_free = max(Decimal("0.00"), FREE_SHIPPING_THRESHOLD - subtotal)
        return render_template(
            "cart.html",
            items=items,
            subtotal=subtotal,
            shipping=shipping,
            total=total,
            remaining_free=remaining_free,
        )

    @app.route("/panier/ajouter", methods=["POST"])
    def cart_add():
        product_id = request.form.get("product_id", type=int)
        quantity = max(1, request.form.get("quantity", 1, type=int))
        product = db.session.get(Product, product_id) if product_id else None
        if not product:
            flash("Produit introuvable.", "error")
            return redirect(url_for("catalogue"))

        if product.stock <= 0:
            flash("Cette boîte à musique est actuellement en rupture de stock.", "warning")
            return redirect(url_for("product_detail", slug=product.slug))

        cart = dict(session.get("cart", {}))
        key = str(product.id)
        new_qty = min(product.stock, int(cart.get(key, 0)) + quantity)
        cart[key] = new_qty
        session["cart"] = cart
        flash(f"« {product.name} » ajouté au panier ({new_qty}).", "success")
        return redirect(request.referrer or url_for("cart_view"))

    @app.route("/panier/modifier", methods=["POST"])
    def cart_update():
        product_id = request.form.get("product_id", type=int)
        quantity = request.form.get("quantity", 1, type=int)
        cart = dict(session.get("cart", {}))
        key = str(product_id)
        if key in cart:
            if quantity <= 0:
                cart.pop(key, None)
            else:
                product = db.session.get(Product, product_id)
                max_q = product.stock if product else quantity
                cart[key] = min(quantity, max_q)
            session["cart"] = cart
        return redirect(url_for("cart_view"))

    @app.route("/panier/supprimer/<int:product_id>", methods=["POST"])
    def cart_remove(product_id: int):
        cart = dict(session.get("cart", {}))
        cart.pop(str(product_id), None)
        session["cart"] = cart
        flash("Article retiré du panier.", "info")
        return redirect(url_for("cart_view"))

    @app.route("/commande/valider", methods=["GET", "POST"])
    def checkout():
        items, subtotal, shipping, total = _build_cart_summary()
        if not items:
            flash("Votre panier est vide.", "warning")
            return redirect(url_for("catalogue"))

        if request.method == "POST":
            customer_name = request.form.get("customer_name", "").strip()
            customer_email = request.form.get("customer_email", "").strip()
            shipping_address = request.form.get("shipping_address", "").strip()
            city = request.form.get("city", "").strip()
            postal_code = request.form.get("postal_code", "").strip()

            if not all([customer_name, customer_email, shipping_address, city, postal_code]):
                flash("Merci de remplir tous les champs de livraison.", "error")
                return render_template(
                    "checkout.html", items=items, subtotal=subtotal, shipping=shipping, total=total
                )

            try:
                order_number = f"KBK-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:5].upper()}"
                order = Order(
                    order_number=order_number,
                    customer_name=customer_name,
                    customer_email=customer_email,
                    shipping_address=shipping_address,
                    city=city,
                    postal_code=postal_code,
                    total_amount=total,
                    status="En attente",
                )
                db.session.add(order)
                db.session.flush()

                for item in items:
                    product = db.session.get(Product, item["product"].id)
                    if not product or product.stock < item["quantity"]:
                        raise ValueError(
                            f"Stock insuffisant pour « {item['product'].name} »."
                        )
                    product.stock -= item["quantity"]
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=item["quantity"],
                        unit_price=product.price,
                    )
                    db.session.add(order_item)

                db.session.commit()
                session["cart"] = {}
                return redirect(url_for("order_confirmation", order_number=order.order_number))
            except Exception as exc:
                db.session.rollback()
                flash(f"Impossible de valider la commande : {exc}", "error")

        return render_template(
            "checkout.html",
            items=items,
            subtotal=subtotal,
            shipping=shipping,
            total=total,
        )

    @app.route("/commande/confirmation/<order_number>")
    def order_confirmation(order_number: str):
        order = Order.query.filter_by(order_number=order_number).first_or_404()
        return render_template("order_confirmation.html", order=order)

    # ------------------------------------------------------------------
    # Configuration 100 % Visuelle (/setup + APIs)
    # ------------------------------------------------------------------
    @app.route("/setup")
    def setup_page():
        return render_template("setup.html")

    def _extract_uri_from_payload(data: dict) -> tuple[str, str]:
        mode = (data.get("mode") or "fields").strip()
        if mode == "sqlite":
            return DEFAULT_SQLITE_URI, "sqlite"
        if mode == "uri":
            raw_uri = data.get("uri", "")
            return normalize_db_uri(raw_uri), "mariadb"
        # mode == "fields"
        uri = build_mariadb_uri(
            host=data.get("host", "127.0.0.1"),
            port=data.get("port", 3306),
            database=data.get("database", "atelier_kibako"),
            user=data.get("user", "root"),
            password=data.get("password", ""),
        )
        return uri, "mariadb"

    @app.route("/api/setup/test-db", methods=["POST"])
    def api_setup_test_db():
        data = request.get_json(silent=True) or {}
        try:
            uri, _ = _extract_uri_from_payload(data)
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc), "advice": "Vérifiez les paramètres saisis."}), 400

        result = test_database_connection(uri)
        status_code = 200 if result.get("ok") else 400
        return jsonify(result), status_code

    @app.route("/api/setup/save", methods=["POST"])
    def api_setup_save():
        data = request.get_json(silent=True) or {}
        seed_demo = bool(data.get("seed_demo", True))

        try:
            uri, db_mode = _extract_uri_from_payload(data)
            ensure_database_exists(uri)
            save_env_config(uri, db_mode=db_mode)
            hot_swap_engine(uri, db_mode=db_mode)

            cats_created, prods_created = (0, 0)
            if seed_demo:
                with app.app_context():
                    cats_created, prods_created = seed_catalog()

            return jsonify(
                {
                    "ok": True,
                    "message": "Configuration enregistrée, schéma ORM créé et moteur SQLAlchemy basculé à chaud.",
                    "db_mode": db_mode,
                    "masked_uri": mask_uri(uri),
                    "seeded": seed_demo,
                    "categories_created": cats_created,
                    "products_created": prods_created,
                }
            )
        except Exception as exc:
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": str(exc),
                        "advice": "Testez d'abord la connexion pour diagnostiquer les droits ou l'hôte MariaDB.",
                    }
                ),
                400,
            )

    # ------------------------------------------------------------------
    # Administration (/admin)
    # ------------------------------------------------------------------
    @app.route("/admin")
    def admin_dashboard():
        db_ok, _ = check_db_ready()
        if not db_ok:
            flash("Initialisez d'abord la base de données via /setup.", "warning")
            return redirect(url_for("setup_page"))

        products = Product.query.order_by(Product.id.desc()).all()
        categories = Category.query.order_by(Category.name.asc()).all()
        orders = Order.query.order_by(Order.created_at.desc()).all()
        revenue = sum((Decimal(str(o.total_amount)) for o in orders if o.status != "Annulée"), Decimal("0.00"))

        return render_template(
            "admin.html",
            products=products,
            categories=categories,
            orders=orders,
            order_statuses=ORDER_STATUSES,
            revenue=revenue,
        )

    @app.route("/admin/produits/ajouter", methods=["POST"])
    def admin_add_product():
        name = request.form.get("name", "").strip()
        universe = request.form.get("universe", "").strip()
        melody_title = request.form.get("melody_title", "").strip()
        wood_type = request.form.get("wood_type", "").strip()
        mechanism = request.form.get("mechanism", "").strip()
        price = request.form.get("price", type=float)
        stock = request.form.get("stock", 10, type=int)
        category_id = request.form.get("category_id", type=int)
        image_url = request.form.get("image_url", "").strip() or "/static/images/hero_atelier_kibako.jpg"
        description = request.form.get("description", "").strip()
        featured = bool(request.form.get("featured"))

        if not all([name, universe, melody_title, wood_type, mechanism, price, category_id, description]):
            flash("Tous les champs obligatoires doivent être renseignés.", "error")
            return redirect(url_for("admin_dashboard"))

        base_slug = _slugify(f"{universe}-{name}")
        slug = base_slug
        if Product.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{uuid.uuid4().hex[:4]}"

        default_notes = [
            {"note": "C5", "freq": 523.25, "dur": 0.4},
            {"note": "E5", "freq": 659.25, "dur": 0.4},
            {"note": "G5", "freq": 783.99, "dur": 0.4},
            {"note": "C6", "freq": 1046.50, "dur": 0.7},
        ]

        product = Product(
            name=name,
            slug=slug,
            universe=universe,
            melody_title=melody_title,
            melody_notes=default_notes,
            wood_type=wood_type,
            mechanism=mechanism,
            price=Decimal(str(round(price, 2))),
            stock=max(0, stock),
            image_url=image_url,
            description=description,
            featured=featured,
            category_id=category_id,
        )
        db.session.add(product)
        db.session.commit()
        flash(f"Boîte à musique « {product.name} » ajoutée au catalogue.", "success")
        return redirect(url_for("admin_dashboard"))

    @app.route("/admin/produits/<int:product_id>/supprimer", methods=["POST"])
    def admin_delete_product(product_id: int):
        product = db.session.get(Product, product_id)
        if not product:
            flash("Produit introuvable.", "error")
            return redirect(url_for("admin_dashboard"))
        if product.order_items:
            flash(
                "Impossible de supprimer un produit déjà présent dans une commande. Mettez son stock à 0.",
                "warning",
            )
            return redirect(url_for("admin_dashboard"))
        db.session.delete(product)
        db.session.commit()
        flash(f"Produit « {product.name} » supprimé.", "info")
        return redirect(url_for("admin_dashboard"))

    @app.route("/admin/commandes/<int:order_id>/statut", methods=["POST"])
    def admin_update_order_status(order_id: int):
        order = db.session.get(Order, order_id)
        new_status = request.form.get("status", "").strip()
        if not order or new_status not in ORDER_STATUSES:
            flash("Commande ou statut invalide.", "error")
            return redirect(url_for("admin_dashboard"))
        order.status = new_status
        db.session.commit()
        flash(f"Statut de la commande {order.order_number} mis à jour : {new_status}.", "success")
        return redirect(url_for("admin_dashboard"))

    @app.route("/admin/seed", methods=["POST"])
    def admin_seed():
        cats, prods = seed_catalog()
        flash(f"Catalogue peuplé : {cats} catégorie(s) et {prods} produit(s) ajoutés.", "success")
        return redirect(url_for("admin_dashboard"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
