###################################### Importing Required Libraries ###################################
from . import db
from datetime import datetime

###################################### Delivery Model #################################################
class Delivery(db.Model):
    __tablename__ = 'deliveries'
    delivery_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    delivery_status = db.Column(db.Enum('Pending', 'Out for Delivery', 'Delivered', 'Cancelled'), nullable=False)
    delivery_address = db.Column(db.String(255), nullable=False)
    delivery_time = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
