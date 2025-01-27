###################################### Importing Required Libraries ###################################
from . import db
from datetime import datetime, timezone
from sqlalchemy.dialects.mysql import LONGBLOB
import uuid
import pytz

###################################### Admin Model ####################################################
class Admin(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    image = db.Column(LONGBLOB, nullable=True)
    status = db.Column(db.Boolean, nullable=True, default=False)
    online_status = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))

    ###################################### Admin Model Constructor ####################################
    def __repr__(self):
        return f'<Admin {self.name}>'
    
    ###################################### Decrator for session token #################################
    @staticmethod
    def generate_session_token():
        return str(uuid.uuid4())
    
    ###################################### Update Last See ############################################
    def update_last_seen(self):
        self.last_seen = datetime.now(pytz.timezone('Asia/Kolkata'))
        