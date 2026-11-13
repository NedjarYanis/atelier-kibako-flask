from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from models import Category, Product, db

shop_bp = Blueprint("shop", __name__)


@shop_bp.route("/")
def index():
    db_ok, _ = current_app.extensions["check_db_ready"]()
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


@shop_bp.route("/catalogue")
def catalogue():
    db_ok, _ = current_app.extensions["check_db_ready"]()
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


@shop_bp.route("/produit/<slug>")
def product_detail(slug: str):
    db_ok, _ = current_app.extensions["check_db_ready"]()
    if not db_ok:
        flash("Veuillez initialiser la base de données via /setup.", "warning")
        return redirect(url_for("setup.setup_page"))

    product = Product.query.filter_by(slug=slug).first_or_404()
    related = (
        Product.query.filter(Product.category_id == product.category_id, Product.id != product.id)
        .limit(3)
        .all()
    )
    return render_template("product.html", product=product, related=related)
