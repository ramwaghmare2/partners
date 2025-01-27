###################################### Importing Required Libraries ###################################
from flask import Blueprint, request, session

###################################### Blueprint for User Activity Tracking ###########################
user_bp = Blueprint('user_bp', __name__, static_folder='../static')

###################################### Middleware for Tracking Login ##################################
@user_bp.before_request
def track_user_actions():
    user_id = session.get('user_id')
    session_id = session.get('session_id')
    role = session.get('role')
    if user_id and session_id and role:
        log_user_activity(
            user_id=user_id,
            session_id=session_id,
            action=request.endpoint,
            details=str(request.args) or str(request.json),
            ip_address=request.remote_addr,
            browser_info=request.user_agent.string,
            role=role
        )


####################################### Logging Helper Function #######################################
def log_user_activity(user_id, session_id, action, details, ip_address, browser_info, role):
    from models import db, ActivityLog  # Assuming SQLAlchemy models
    log_entry = ActivityLog(
        user_id=user_id,
        session_id=session_id,
        action=action,
        details=details,
        ip_address=ip_address,
        browser_info=browser_info,
        role = role
    )
    db.session.add(log_entry)
    db.session.commit()

####################################### Summary After Logout ##########################################
def generate_session_summary(user_id, session_id, timestamp):
    from models import ActivityLog
    logs = ActivityLog.query.filter_by(user_id=user_id, session_id=session_id).all()
    summary = [{"action_type": log.action_type, "timestamp": log.timestamp, "details": log.details} for log in logs]
    return summary

######################################### Log Encryption (for Sensitive Data) #########################
from cryptography.fernet import Fernet

# Generate a key (do this once and securely store it)
key = Fernet.generate_key()
cipher_suite = Fernet(key)

def encrypt_log_details(details):
    return cipher_suite.encrypt(details.encode('utf-8')).decode('utf-8')

def decrypt_log_details(encrypted_details):
    return cipher_suite.decrypt(encrypted_details.encode('utf-8')).decode('utf-8')

# Example: Encrypt details before storing in the database
encrypted_details = encrypt_log_details('User performed action X')

# Example: Decrypt details when retrieving them
decrypted_details = decrypt_log_details(encrypted_details)
