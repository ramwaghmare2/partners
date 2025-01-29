###################################### Importing Required Libraries ###################################
from . import db
from datetime import datetime, timezone
from sqlalchemy.dialects.mysql import LONGBLOB
from .super_distributor import SuperDistributor
import pytz

###################################### Distributor Model ##############################################
class Distributor(db.Model):
    __tablename__ = 'distributors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(20), nullable=True)
    super_distributor = db.Column(db.Integer, db.ForeignKey('super_distributors.id'), nullable=True)  # Foreign key column
    status = db.Column(db.Enum('activated', 'deactivated'), default='activated')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    image = db.Column(LONGBLOB, nullable=True)
    online_status = db.Column(db.Boolean, nullable=True, default=False)
    
    ###################################### Relationship with SuperDistributor and Kitchen Model #######
    super_distributor_relation = db.relationship('SuperDistributor', back_populates='distributors', lazy=True, foreign_keys=[super_distributor])
    kitchens = db.relationship('Kitchen', backref='distributors', lazy=True)
    
    ###################################### Distributor Model Constructor ##############################
    def __repr__(self):
        return f'<Distributor {self.name}>'
