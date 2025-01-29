###################################### Importing Required Libraries ###################################
from . import db
from extensions import bcrypt
from sqlalchemy.dialects.mysql import LONGBLOB
from datetime import datetime, timezone
import pytz

###################################### Kitchen Model ##################################################
class Kitchen(db.Model):
    __tablename__ = 'kitchens'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(15), nullable=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    order_id = db.Column(db.Integer, nullable=True)
    state = db.Column(db.String(50), nullable=True)
    pin_code = db.Column(db.String(6), nullable=True)
    district = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    image = db.Column(LONGBLOB,nullable=True)
    status = db.Column(db.Enum('activated', 'deactivated'), default='activated')
    online_status = db.Column(db.Boolean, nullable=True, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    
    ###################################### Relationship with FoodItem and Sales Model #################
    food_items = db.relationship('FoodItem', backref='kitchen', lazy=True)
    sales = db.relationship('Sales', backref='kitchen', lazy=True)


    ###################################### Function for setting password ##############################
    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    ###################################### Function for checking password #############################
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    ###################################### Kitchen Model Constructor ##################################
    def __repr__(self):
        return f'<kitchens {self.name}>'
    
    ###################################### Validate Pin Code ##########################################
    @staticmethod
    def validate_pin_code(pin_code):
        return len(pin_code) == 6 and pin_code.isdigit()