from flask import Blueprint, current_app, jsonify

from models import Category, Order, Product, db

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


@api_bp.route("/health")
def health():
    db_ok, msg = current_app.extensions["check_db_ready"]()
    return jsonify(
        {
            "status": "ok" if db_ok else "degraded",
            "db_ready": db_ok,
            "db_mode": current_app.config.get("DB_MODE"),
            "message": msg or "ORM opérationnel",
        }
    )


@api_bp.route("/products")
def list_products():
    db_ok, _ = current_app.extensions["check_db_ready"]()
    if not db_ok:
        return jsonify({"products": []})

    products = Product.query.order_by(Product.id.asc()).all()
    return jsonify(
        {
            "count": len(products),
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "slug": p.slug,
                    "universe": p.universe,
                    "melody_title": p.melody_title,
                    "melody_notes": p.melody_notes,
                    "wood_type": p.wood_type,
                    "mechanism": p.mechanism,
                    "price": float(p.price),
                    "stock": p.stock,
                    "image_url": p.image_url,
                    "category": p.category.name if p.category else None,
                }
                for p in products
            ],
        }
    )


@api_bp.route("/telemetry")
def telemetry():
    """Données agrégées pour les graphiques Chart.js du tableau de bord."""
    db_ok, _ = current_app.extensions["check_db_ready"]()
    if not db_ok:
        return jsonify({"ok": False, "woods": [], "categories": []})

    products = Product.query.all()
    orders = Order.query.all()
    categories = Category.query.all()

    wood_stock = {}
    for p in products:
        wood_stock[p.wood_type] = wood_stock.get(p.wood_type, 0) + p.stock

    cat_counts = {c.name: len(c.products) for c in categories}

    status_counts = {}
    for o in orders:
        status_counts[o.status] = status_counts.get(o.status, 0) + 1

    return jsonify(
        {
            "ok": True,
            "wood_stock": {
                "labels": list(wood_stock.keys()),
                "values": list(wood_stock.values()),
            },
            "categories": {
                "labels": list(cat_counts.keys()),
                "values": list(cat_counts.values()),
            },
            "order_statuses": {
                "labels": list(status_counts.keys()),
                "values": list(status_counts.values()),
            },
        }
    )
