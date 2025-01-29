###################################### Importing Required Libraries ###################################
from . import db
from datetime import datetime, timezone
from extensions import bcrypt
from sqlalchemy.dialects.mysql import LONGBLOB
import pytz

###################################### Manager Model ##################################################
class Manager(db.Model):
    __tablename__ = 'managers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    image = db.Column(LONGBLOB,nullable=True)
    status = db.Column(db.Enum('activated', 'deactivated'), default='activated')
    online_status = db.Column(db.Boolean, nullable=True, default=False)
    
    ###################################### Relationship with SuperDistributor Model ###################
    super_distributors = db.relationship('SuperDistributor', backref='manager', lazy=True)
    

    ###################################### Function to set password ###################################
    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    ###################################### Function to check passowrd #################################
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    ###################################### Manager Model Constructor ##################################
    def __repr__(self):
        return f'<Manager {self.name}>'
    
