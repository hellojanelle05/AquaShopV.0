from . import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


###############################################
# CUSTOMER MODEL
###############################################
class Customer(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(100))
    password_hash = db.Column(db.String(150))
    date_joined = db.Column(db.DateTime(), default=datetime.utcnow)

    # Relationships
    cart_items = db.relationship('Cart', backref='customer', lazy=True)
    orders = db.relationship('Order', backref='customer', lazy=True)

    @property
    def password(self):
        raise AttributeError('Password is not readable.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Customer {self.username}>"


###############################################
# PRODUCT MODEL
###############################################
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    previous_price = db.Column(db.Float, nullable=False)
    in_stock = db.Column(db.Integer, nullable=False)
    product_picture = db.Column(db.String(1000), nullable=False)
    flash_sale = db.Column(db.Boolean, default=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    carts = db.relationship('Cart', backref='product', lazy=True)
    items = db.relationship('OrderItem', backref='product_info', lazy=True)

    def __repr__(self):
        return f"<Product {self.product_name}>"


###############################################
# CART MODEL
###############################################
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)

    customer_link = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_link = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

    def __repr__(self):
        return f"<Cart {self.id}>"


###############################################
# ORDER MODEL
###############################################
class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)

    total_price = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))
    status = db.Column(db.String(50), default="Pending")

    payment_reference = db.Column(db.String(200), nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship: Order → OrderItems
    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order {self.id}>"


###############################################
# ORDER ITEM MODEL
###############################################
class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

    quantity = db.Column(db.Integer, nullable=False)
    price_each = db.Column(db.Float, nullable=False)  # copy of price at order time

    # product relationship
    product = db.relationship("Product")

    def __repr__(self):
        return f"<OrderItem {self.id} - Order {self.order_id}>"
