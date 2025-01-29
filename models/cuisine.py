###################################### Importing Required Libraries ###################################
from . import db
from datetime import datetime, timezone
from sqlalchemy.dialects.mysql import LONGBLOB
import pytz

###################################### Cuisine Model ##################################################
class Cuisine(db.Model):
    __tablename__ = 'cuisines'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    image = db.Column(LONGBLOB,nullable=True)

    ###################################### Relationship with FoodItem and Sales Model #################
    food_items = db.relationship('FoodItem', backref='cuisine', lazy=True)
    sales = db.relationship('Sales', backref='cuisine', lazy=True)

    ###################################### Cuisine Model Constructor ##################################
    def __repr__(self):
        return f'<Cuisine {self.name}>'