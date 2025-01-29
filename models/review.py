###################################### Importing Required Libraries ###################################
from . import db
from datetime import datetime
from models.customer import Customer
#from .menu_item import MenuItem
#from models.restaurant import Restaurant

###################################### Review Model ###################################################
class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('customer.customer_id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('kitchens.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ######################## Relationship with User, Restaurant and MenuItem ####################
    user = db.relationship('Customer', back_populates='reviews')
    restaurant = db.relationship('Kitchen', back_populates='reviews')
    menu_item = db.relationship('FoodItem', back_populates='reviews')

"""
#Setting up relationships back_populates for the Review model
#Customer.reviews = db.relationship('Review', back_populates='user')
#Restaurant.reviews = db.relationship('Review', back_populates='restaurant')
#MenuItem.reviews = db.relationship('Review', back_populates='menu_item')

"""