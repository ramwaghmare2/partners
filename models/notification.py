###################################### Importing Required Libraries ###################################
from . import db
from datetime import datetime
import pytz

###################################### Notification Model #############################################
class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # Foreign Key to Users
    role = db.Column(db.String(50), nullable=True)   # Role (Admin, Manager, etc.)
    notification_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))

    ###################################### Function to return Notification as Dictionary ##############
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'role': self.role,
            'notification_type': self.notification_type,
            'description': self.description,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
