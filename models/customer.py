###################################### Importing Required Libraries ###################################
from . import db
from datetime import datetime, timedelta
from random import randint

###################################### User Model #####################################################
class Customer(db.Model):
    __tablename__ = 'customer'
    customer_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(512), nullable=False)
    mobile_number = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    otp = db.Column(db.String(6), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    otp_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ############################### Relationship with Order and Review ################################
    orders = db.relationship('Order', backref='customer', lazy=True)
    reviews = db.relationship('Review', backref='customer', lazy=True)

    ###################################### OTP Generation Function ####################################
    def generate_otp(self):
        """Generate and save OTP with an expiration time."""
        self.otp = f"{randint(100000, 999999)}"
        self.otp_expiry = datetime.utcnow() + timedelta(minutes=5)

    ###################################### Function For OTP Verification ##############################
    def verify_otp(self, otp):
        """Verify the OTP."""
        return self.otp == otp and datetime.utcnow() < self.otp_expiry