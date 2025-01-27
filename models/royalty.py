###################################### Importing Required Libraries ###################################
from . import db
from datetime import datetime
import pytz

###################################### Royalty Settings Model #########################################
class RoyaltySettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)
    royalty_percentage = db.Column(db.Float, default=20.0)
    
###################################### Royalty Wallet Model ###########################################
class RoyaltyWallet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entity_id = db.Column(db.Integer, nullable=False)
    role = db.Column(db.String(50), nullable=False)
    royalty_amount = db.Column(db.Float, default=0.0)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    