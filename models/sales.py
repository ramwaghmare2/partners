###################################### Importing Required Libraries ###################################
from . import db
from datetime import datetime
import pytz

###################################### Sales Model ####################################################
class Sales(db.Model):
    __tablename__ = 'sales'

    sale_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    kitchen_id = db.Column(db.Integer, db.ForeignKey('kitchens.id'), nullable=True)
    cuisine_id = db.Column(db.Integer, db.ForeignKey('cuisines.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=False)
    payment_mode = db.Column(db.Enum('COD', 'UPI', 'Credit Card', 'Debit Card'), nullable=True)
    datetime = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))

    ###################################### Sales Model Constructor ####################################
    def __repr__(self):
        return f'<Sales sale_id={self.sale_id}, order_id={self.order_id}>'
