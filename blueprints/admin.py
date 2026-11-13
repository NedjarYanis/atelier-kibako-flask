from decimal import Decimal
import re
import uuid

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from models import Category, Order, Product, db, seed_catalog

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

ORDER_STATUSES = ["En attente", "En préparation", "Expédiée", "Livrée", "Annulée"]


def _slugify(text_val: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (text_val or "").lower()).strip("-")
    return slug or f"kibako-{uuid.uuid4().hex[:6]}"


@admin_bp.route("")
@admin_bp.route("/")
def admin_dashboard():
    db_ok, _ = current_app.extensions["check_db_ready"]()
    if not db_ok:
        flash("Initialisez d'abord la base de données via /setup.", "warning")
        return redirect(url_for("setup.setup_page"))

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


@admin_bp.route("/produits/ajouter", methods=["POST"])
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
        return redirect(url_for("admin.admin_dashboard"))

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
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/produits/<int:product_id>/supprimer", methods=["POST"])
def admin_delete_product(product_id: int):
    product = db.session.get(Product, product_id)
    if not product:
        flash("Produit introuvable.", "error")
        return redirect(url_for("admin.admin_dashboard"))
    if product.order_items:
        flash(
            "Impossible de supprimer un produit déjà présent dans une commande. Mettez son stock à 0.",
            "warning",
        )
        return redirect(url_for("admin.admin_dashboard"))
    db.session.delete(product)
    db.session.commit()
    flash(f"Produit « {product.name} » supprimé.", "info")
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/commandes/<int:order_id>/statut", methods=["POST"])
def admin_update_order_status(order_id: int):
    order = db.session.get(Order, order_id)
    new_status = request.form.get("status", "").strip()
    if not order or new_status not in ORDER_STATUSES:
        flash("Commande ou statut invalide.", "error")
        return redirect(url_for("admin.admin_dashboard"))
    order.status = new_status
    db.session.commit()
    flash(f"Statut de la commande {order.order_number} mis à jour : {new_status}.", "success")
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/seed", methods=["POST"])
def admin_seed():
    cats, prods = seed_catalog()
    flash(f"Catalogue peuplé : {cats} catégorie(s) et {prods} produit(s) ajoutés.", "success")
    return redirect(url_for("admin.admin_dashboard"))
