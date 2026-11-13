from datetime import datetime, timezone
from decimal import Decimal
import uuid

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from models import Order, OrderItem, Product, db

cart_bp = Blueprint("cart", __name__)

FREE_SHIPPING_THRESHOLD = Decimal("80.00")
STANDARD_SHIPPING_COST = Decimal("6.90")


def _build_cart_summary():
    cart = session.get("cart", {})
    items = []
    subtotal = Decimal("0.00")
    db_ok, _ = current_app.extensions["check_db_ready"]()
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


@cart_bp.route("/panier")
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


@cart_bp.route("/panier/ajouter", methods=["POST"])
def cart_add():
    product_id = request.form.get("product_id", type=int)
    quantity = max(1, request.form.get("quantity", 1, type=int))
    product = db.session.get(Product, product_id) if product_id else None
    if not product:
        flash("Produit introuvable.", "error")
        return redirect(url_for("shop.catalogue"))

    if product.stock <= 0:
        flash("Cette boîte à musique est actuellement en rupture de stock.", "warning")
        return redirect(url_for("shop.product_detail", slug=product.slug))

    cart = dict(session.get("cart", {}))
    key = str(product.id)
    new_qty = min(product.stock, int(cart.get(key, 0)) + quantity)
    cart[key] = new_qty
    session["cart"] = cart
    flash(f"« {product.name} » ajouté au panier ({new_qty}).", "success")
    return redirect(request.referrer or url_for("cart.cart_view"))


@cart_bp.route("/panier/modifier", methods=["POST"])
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
    return redirect(url_for("cart.cart_view"))


@cart_bp.route("/panier/supprimer/<int:product_id>", methods=["POST"])
def cart_remove(product_id: int):
    cart = dict(session.get("cart", {}))
    cart.pop(str(product_id), None)
    session["cart"] = cart
    flash("Article retiré du panier.", "info")
    return redirect(url_for("cart.cart_view"))


@cart_bp.route("/commande/valider", methods=["GET", "POST"])
def checkout():
    items, subtotal, shipping, total = _build_cart_summary()
    if not items:
        flash("Votre panier est vide.", "warning")
        return redirect(url_for("shop.catalogue"))

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
            return redirect(url_for("cart.order_confirmation", order_number=order.order_number))
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


@cart_bp.route("/commande/confirmation/<order_number>")
def order_confirmation(order_number: str):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    return render_template("order_confirmation.html", order=order)
