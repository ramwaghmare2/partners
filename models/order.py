###################################### Importing Required Libraries ###################################
from . import db
from datetime import datetime

###################################### Order Model ####################################################
class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('customer.customer_id'), nullable=False)
    kitchen_id = db.Column(db.Integer, db.ForeignKey('kitchens.id'), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    order_status = db.Column(db.Enum('Pending', 'Processing', 'Completed', 'Cancelled'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    month = db.Column(db.Integer) #New Column
    day_of_week = db.Column(db.Integer) #New Column

    ############################ Relationship with Orderitem, Payment and Delivery ####################
    order_items = db.relationship('OrderItem', backref='order', lazy=True)
    payment = db.relationship('Payment', uselist=False, backref='order')
    delivery = db.relationship('Delivery', uselist=False, backref='order')

