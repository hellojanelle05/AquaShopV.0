from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from .models import Product, Cart, Order, OrderItem
from . import db
from datetime import datetime

views = Blueprint('views', __name__)


########################################
# AJAX — PLUS CART
########################################
@views.route('/pluscart')
@login_required
def plus_cart():
    item_id = request.args.get('item_id')
    cart_item = Cart.query.get(int(item_id))

    cart_item.quantity += 1
    db.session.commit()

    cart_items = Cart.query.filter_by(customer_link=current_user.id).all()

    amount = sum(i.quantity * i.product.current_price for i in cart_items)
    total = amount

    return jsonify({
        'quantity': cart_item.quantity,
        'amount': amount,
        'total': total
    })


########################################
# AJAX — MINUS CART
########################################
@views.route('/minuscart')
@login_required
def minus_cart():
    item_id = request.args.get('item_id')
    cart_item = Cart.query.get(int(item_id))

    if cart_item.quantity > 1:
        cart_item.quantity -= 1

    db.session.commit()

    cart_items = Cart.query.filter_by(customer_link=current_user.id).all()

    amount = sum(i.quantity * i.product.current_price for i in cart_items)
    total = amount

    return jsonify({
        'quantity': cart_item.quantity,
        'amount': amount,
        'total': total
    })


########################################
# HOME PAGE
########################################
@views.route('/')
def home():

    # Admin redirect → Admin Dashboard
    if current_user.is_authenticated and current_user.id == 1:
        return redirect(url_for('views.admin_page'))

    items = Product.query.all()
    return render_template("home.html", items=items)

########################################
# OUR STORY PAGE
########################################
@views.route('/story')
def story_page():
    cart_length = 0

    if current_user.is_authenticated:
        if current_user.id == 1:
            return redirect(url_for('views.admin_orders'))

        cart_length = Cart.query.filter_by(customer_link=current_user.id).count()

    return render_template("story.html", cart=list(range(cart_length)))

########################################
# ADD TO CART
########################################
@views.route("/add-to-cart/<int:product_id>")
@login_required
def add_to_cart(product_id):

    # BLOCK ADMIN FROM ORDERING
    if current_user.id == 1:
        flash("Admins cannot place orders.", "warning")
        return redirect(url_for('views.admin_orders'))

    product = Product.query.get_or_404(product_id)

    existing = Cart.query.filter_by(
        customer_link=current_user.id,
        product_link=product_id
    ).first()

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

    # BLOCK ADMIN FROM CART
    if current_user.id == 1:
        return redirect(url_for('views.admin_orders'))

    cart_items = Cart.query.filter_by(customer_link=current_user.id).all()
    amount = sum(item.quantity * item.product.current_price for item in cart_items)
    total = amount

    return render_template(
        "cart.html",
        cart=cart_items,
        amount=amount,
        total=amount
    )


########################################
# REMOVE FROM CART
########################################
@views.route("/remove-from-cart/<int:item_id>")
@login_required
def remove_from_cart(item_id):
    item = Cart.query.filter_by(
        id=item_id,
        customer_link=current_user.id
    ).first()

    if item:
        db.session.delete(item)
        db.session.commit()
        flash("Item removed from cart!", "success")
    else:
        flash("Item not found!", "danger")

    return redirect(url_for('views.cart'))



########################################
# UPDATE CART — AJAX
########################################
@views.route("/update-cart", methods=["POST"])
@login_required
def update_cart():
    item_id = request.form.get("item_id")
    action = request.form.get("action")

    item = Cart.query.filter_by(
        id=item_id,
        customer_link=current_user.id
    ).first()

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

    return jsonify({
        "success": True,
        "quantity": item.quantity
    })


########################################
# CHECKOUT PAGE
########################################
@views.route("/checkout")
@login_required
def checkout():

    if current_user.id == 1:
        return redirect(url_for('views.admin_orders'))

    cart_items = Cart.query.filter_by(customer_link=current_user.id).all()

    if not cart_items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for('views.cart'))

    total_amount = sum(
        item.quantity * item.product.current_price for item in cart_items
    )

    return render_template("checkout.html", cart=cart_items, total=total_amount)

########################################
# PLACE ORDER — FINAL
########################################
@views.route("/place-order", methods=["POST"])
@login_required
def place_order():

    # BLOCK ADMIN
    if current_user.id == 1:
        return redirect(url_for('views.admin_orders'))

    payment_method = request.form.get("payment_method")

    # Get items in cart
    cart_items = Cart.query.filter_by(customer_link=current_user.id).all()

    if not cart_items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("views.cart"))

    # Compute total amount
    total_amount = sum(item.quantity * item.product.current_price for item in cart_items)

    # Create order
    new_order = Order(
        customer_id=current_user.id,
        total_price=total_amount,
        status="pending",
        payment_method=payment_method,
        date_created=datetime.utcnow()
    )

    db.session.add(new_order)
    db.session.flush()

    # PROCESS EACH ITEM
    for item in cart_items:

        # 1. Get actual product
        product = Product.query.get(item.product_link)

        # STOCK CHECK
        if product.in_stock < item.quantity:
            flash(f"Insufficient stock for {product.product_name}.", "danger")
            db.session.rollback()
            return redirect(url_for("views.checkout"))

        # 3. Deduct stock
        product.in_stock -= item.quantity
        db.session.add(product)

        # 4. Create Order Item entry
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item.product_link,
            quantity=item.quantity,
            price_each=item.product.current_price
        )
        db.session.add(order_item)

    # 5. Clear cart
    Cart.query.filter_by(customer_link=current_user.id).delete()

    # 6. Final commit
    db.session.commit()

    flash("Order placed successfully!", "success")
    return redirect(url_for("views.orders"))



########################################
# USER — VIEW ORDERS
########################################
@views.route("/orders")
@login_required
def orders():

    if current_user.id == 1:
        return redirect(url_for('views.admin_orders'))

    orders = Order.query.filter_by(customer_id=current_user.id)\
                        .order_by(Order.date_created.desc())\
                        .all()

    return render_template("orders.html", orders=orders)


########################################
# USER — ORDER DETAILS
########################################
@views.route("/order/<int:order_id>")
@login_required
def order_details(order_id):

    order = Order.query.filter_by(
        id=order_id,
        customer_id=current_user.id
    ).first_or_404()

    items = OrderItem.query.filter_by(order_id=order_id).all()

    return render_template("order_details.html", order=order, items=items)

########################################
# ADMIN — VIEW ALL ORDERS
########################################
@views.route("/admin/orders")
@login_required
def admin_orders():

    if current_user.id != 1:
        return redirect(url_for('views.home'))

    orders = Order.query.order_by(Order.date_created.desc()).all()
    return render_template("view_orders.html", orders=orders)


########################################
# ADMIN — UPDATE ORDER STATUS
########################################
@views.route("/admin/order/<int:order_id>/update", methods=["GET", "POST"])
@login_required
def update_order_status(order_id):

    if current_user.id != 1:
        return redirect(url_for('views.home'))

    order = Order.query.get_or_404(order_id)

    if request.method == "POST":
        new_status = request.form.get("status")
        if new_status:
            order.status = new_status
            db.session.commit()
            flash("Order status updated!", "success")
            return redirect(url_for("views.admin_orders"))

    return render_template("update_item.html", order=order)

########################################
# SEARCH
########################################
@views.route('/search', methods=['POST'])
def search():
    query = request.form.get('search', '').strip()

    if not query:
        flash("Please enter a search term.", "warning")
        return redirect(request.referrer)

    # FIND ITEMS MATCHING SEARCH
    items = Product.query.filter(
        Product.product_name.ilike(f"%{query}%")
    ).all()

    return render_template("search.html", items=items)

########################################
# ADMIN PAGE / DASHBOARD
########################################
@views.route('/admin-page')
@login_required
def admin_page():

    if current_user.id != 1:
        return redirect(url_for('views.home'))

    return render_template("admin.html")
