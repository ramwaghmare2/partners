###################################### Importing Required Libraries ###################################
from . import db
from datetime import datetime
from pytz import timezone as pytz_timezone

###################################### Activity Log Model #############################################
def kolkata_time(): # Use pytz for timezone-aware datetime 
    dt = datetime.now(pytz_timezone('Asia/Kolkata')) # Convert the datetime object to a naive datetime (without timezone) 
    naive_dt = dt.replace(tzinfo=None) 
    return naive_dt

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=kolkata_time, nullable=False)
    details = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    browser_info = db.Column(db.String(255), nullable=True)
    session_id = db.Column(db.String(255), nullable=True)
