###################################### Importing Required Libraries ###################################
from . import db
from datetime import datetime, timezone
import pytz

###################################### Order Model ####################################################
class Order(db.Model):
    __tablename__ = 'orders'

    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    kitchen_id = db.Column(db.Integer, db.ForeignKey('kitchens.id'), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    order_status = db.Column(db.Enum('Pending', 'Processing', 'Completed', 'Cancelled'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))

    ############################ Relationship with Sales, OrderItem, Customer and Kitchen Model #######
    sales = db.relationship('Sales', backref='orders', lazy=True)
    customer = db.relationship('Customer', backref='orders')
    kitchen = db.relationship('Kitchen', backref='orders')
    order_items = db.relationship('OrderItem', backref='order', lazy=True)  # Bidirectional link with OrderItem
    # Many-to-Many via OrderItem

    ###################################### Order Model Constructor ####################################
    def __repr__(self):
        return f'<Order {self.order_id}>'

###################################### OrderItem Model ################################################
class OrderItem(db.Model):
    __tablename__ = 'order_items'

    order_item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    ###################################### Relationship with FoodItem Model ###########################
    food_item = db.relationship('FoodItem', back_populates='order_items')  # Bidirectional link with FoodItem
    
    ###################################### OrderItem Model Constructor ################################
    def __repr__(self):
        return f'<OrderItem {self.order_item_id}>'
