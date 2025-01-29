###################################### Importing Required Libraries ###################################
from . import db
from datetime import datetime, timezone
from sqlalchemy.dialects.mysql import LONGBLOB
import pytz

###################################### FoodItem Model #################################################
class FoodItem(db.Model):
    __tablename__ = 'food_items'
    
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Float, nullable=False)
    available = db.Column(db.Boolean, default=True)
    cuisine_id = db.Column(db.Integer, db.ForeignKey('cuisines.id'), nullable=False)
    kitchen_id = db.Column(db.Integer, db.ForeignKey('kitchens.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    image = db.Column(LONGBLOB, nullable=True)
    status = db.Column(db.Enum('activated', 'deactivated'), default='activated', server_default='activated')

    ###################################### Relationship with OrderItem and Sales Model ################
    order_items = db.relationship('OrderItem', back_populates='food_item', lazy='dynamic')
    sales = db.relationship('Sales', backref='food_items', lazy=True)
   
    ###################################### FoodItem Model Constructor #################################
    def __repr__(self):
        return f'<FoodItem {self.item_name}>'
    
    ###################################### Validate Price #############################################
    @staticmethod
    def validate_price(price):
        return price >= 0
