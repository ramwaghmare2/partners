###################################### Importing Required Libraries ###################################
from . import db
from datetime import datetime

###################################### Paymtent Model #################################################
class Payment(db.Model):
    __tablename__ = 'payments'
    payment_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    payment_status = db.Column(db.Enum('Pending', 'Completed', 'Failed'), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
