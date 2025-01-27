###################################### Importing Required Libraries ###################################
from . import db
from datetime import datetime, timezone
from sqlalchemy.dialects.mysql import LONGBLOB
import pytz

###################################### SuperDistributor Model #########################################
class SuperDistributor(db.Model):
    __tablename__ = 'super_distributors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(20), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('managers.id'), nullable=True)
    status = db.Column(db.Enum('activated', 'deactivated'), default='activated')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    image = db.Column(LONGBLOB, nullable=True)
    online_status = db.Column(db.Boolean, nullable=True, default=False)
    
    ###################################### Relationship with Distributor Model ########################
    distributors = db.relationship('Distributor', back_populates='super_distributor_relation', lazy=True)

    ###################################### SuperDistributor Model Constructor #########################
    def __repr__(self):
        return f'<SuperDistributor {self.name}>'
