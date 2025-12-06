from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from .models import Product, Cart, Order, OrderItem
from . import db
from datetime import datetime

views = Blueprint('views', __name__)

########################################
# HOME PAGE
########################################
@views.route('/')
def home():
    items = Product.query.all()
    return render_template("home.html", items=items)


########################################
# ADD TO CART
########################################
@views.route("/add-to-cart/<int:product_id>")
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    existing = Cart.query.filter_by(customer_link=current_user.id, product_link=product_id).first()

    if existing:
        existing.quantity += 1
    else:
        new_item = Cart(
            product_link=product_id,
            customer_link=current_user.id,
            quantity=1
        )
        db.session.add(new_item)

    db.session.commit()
    flash("Added to cart!", "success")
    return redirect(url_for('views.cart'))


########################################
# CART PAGE
########################################
@views.route("/cart")
@login_required
def cart():
    cart_items = Cart.query.filter_by(customer_link=current_user.id).all()
    amount = sum(item.quantity * item.product.current_price for item in cart_items)
    total = amount  # shipping can be added here if needed
    return render_template("cart.html", cart=cart_items, amount=amount, total=total)


########################################
# CHECKOUT → CREATE ORDER
########################################
@views.route("/checkout")
@login_required
def checkout():
    cart_items = Cart.query.filter_by(customer_link=current_user.id).all()
    if not cart_items:
        flash("Your cart is empty", "warning")
        return redirect(url_for('views.cart'))

    total_amount = sum(item.quantity * item.product.current_price for item in cart_items)

    # Create new order
    new_order = Order(
        customer_id=current_user.id,
        total_price=total_amount,
        status="pending",
        payment_method="None"
    )
    db.session.add(new_order)
    db.session.flush()  # ensures new_order.id is available

    # Add order items
    for item in cart_items:
        db.session.add(OrderItem(
            order_id=new_order.id,
            product_id=item.product_link,
            quantity=item.quantity,
            price_each=item.product.current_price
        ))

    # Clear cart
    Cart.query.filter_by(customer_link=current_user.id).delete()
    db.session.commit()

    flash("Order placed successfully!", "success")
    return redirect(url_for('views.orders'))


########################################
# LIST USER ORDERS
########################################
@views.route("/orders")
@login_required
def orders():
    items = (
        OrderItem.query
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.customer_id == current_user.id)
        .all()
    )
    return render_template("orders.html", orders=items)


########################################
# ORDER DETAILS PAGE (USER)
########################################
@views.route("/order/<int:order_id>")
@login_required
def order_details(order_id):
    order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first_or_404()
    items = OrderItem.query.filter_by(order_id=order_id).all()
    return render_template("order_details.html", order=order, items=items)


########################################
# REMOVE FROM CART
########################################
@views.route("/remove-from-cart/<int:item_id>")
@login_required
def remove_from_cart(item_id):
    item = Cart.query.filter_by(id=item_id, customer_link=current_user.id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash("Item removed", "success")
    return redirect(url_for('views.cart'))


########################################
# UPDATE CART QUANTITY (AJAX)
########################################
@views.route("/update-cart", methods=["POST"])
@login_required
def update_cart():
    item_id = request.form.get("item_id")
    action = request.form.get("action")
    item = Cart.query.get(item_id)

    if not item:
        return jsonify({"error": "Item not found"}), 404

    if action == "plus":
        item.quantity += 1
    elif action == "minus":
        item.quantity -= 1
        if item.quantity < 1:
            db.session.delete(item)
            db.session.commit()
            return jsonify({"success": True, "delete": True})

    db.session.commit()
    return jsonify({"success": True, "quantity": item.quantity})


########################################
# ADMIN: VIEW ALL ORDERS
########################################
@views.route("/admin/orders")
@login_required
def admin_orders():
    # TODO: optionally check if current_user is admin
    orders = Order.query.order_by(Order.date_created.desc()).all()
    return render_template("view_orders.html", orders=orders)


########################################
# ADMIN: VIEW ORDER DETAILS
########################################
@views.route("/admin/order/<int:order_id>")
@login_required
def admin_order_details(order_id):
    order = Order.query.get_or_404(order_id)
    items = OrderItem.query.filter_by(order_id=order_id).all()
    return render_template("view_orders.html", order=order, items=items)


########################################
# ADMIN: UPDATE ORDER STATUS
########################################
@views.route("/admin/order/<int:order_id>/update", methods=["GET", "POST"])
@login_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)

    if request.method == "POST":
        new_status = request.form.get("status")
        if new_status:
            order.status = new_status
            db.session.commit()
            flash("Order status updated successfully!", "success")
            return redirect(url_for("views.admin_orders"))

    return render_template("update_item.html", order=order)
