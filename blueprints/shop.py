from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for

from models import Category, Product, db
from themes import SITES, SITES_ORDER

shop_bp = Blueprint("shop", __name__)


def _get_site_or_404(theme: str) -> dict:
    site = SITES.get(theme)
    if not site:
        abort(404)
    return site


def _query_catalogue():
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

    return {
        "products": products,
        "categories": categories,
        "universes": universes,
        "woods": woods,
        "mechanisms": mechanisms,
        "filters": {
            "q": q,
            "category": cat_slug,
            "universe": universe,
            "wood": wood,
            "mechanism": mechanism,
            "sort": sort,
        },
    }


# ----------------------------------------------------------------------
# HUB CENTRAL (Page d'accueil principale /)
# ----------------------------------------------------------------------
@shop_bp.route("/")
def index():
    db_ok, _ = current_app.extensions["check_db_ready"]()
    product_count = Product.query.count() if db_ok else 0
    sites_list = [SITES[k] for k in SITES_ORDER]
    return render_template("hub.html", sites=sites_list, product_count=product_count)


# ----------------------------------------------------------------------
# 5 SITES THÉMATISÉS (/site/<theme>/...)
# ----------------------------------------------------------------------
@shop_bp.route("/site/<theme>/")
def site_index(theme: str):
    site = _get_site_or_404(theme)
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
        site=site,
        featured_products=featured_products,
        categories=categories,
    )


@shop_bp.route("/site/<theme>/catalogue")
def site_catalogue(theme: str):
    site = _get_site_or_404(theme)
    db_ok, _ = current_app.extensions["check_db_ready"]()
    if not db_ok:
        return render_template(
            "catalogue.html",
            site=site,
            products=[],
            categories=[],
            universes=[],
            woods=[],
            mechanisms=[],
            filters={},
        )
    ctx = _query_catalogue()
    return render_template("catalogue.html", site=site, **ctx)


@shop_bp.route("/site/<theme>/produit/<slug>")
def site_product_detail(theme: str, slug: str):
    site = _get_site_or_404(theme)
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
    return render_template("product.html", site=site, product=product, related=related)


# ----------------------------------------------------------------------
# Rétro-compatibilité des routes directes (/catalogue, /produit/<slug>)
# ----------------------------------------------------------------------
@shop_bp.route("/catalogue")
def catalogue():
    return redirect(url_for("shop.site_catalogue", theme="roche-bobois", **request.args))


@shop_bp.route("/produit/<slug>")
def product_detail(slug: str):
    return redirect(url_for("shop.site_product_detail", theme="roche-bobois", slug=slug))
