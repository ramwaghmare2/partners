###################################### Importing Required Libraries ###################################
from models import db, Notification
from models import Admin, Manager, SuperDistributor, Distributor, Kitchen
from datetime import datetime
from app import socketio
from flask import current_app

###################################### Notification Service ###########################################
def get_notification_targets(creator_role, target_role=None):

    # Define role hierarchy
    role_hierarchy = {
        "Admin": ["Manager", "SuperDistributor", "Distributor", "Kitchen"],
        "Manager": ["SuperDistributor", "Distributor", "Kitchen"],
        "SuperDistributor": ["Distributor", "Kitchen"],
        "Distributor": ["Kitchen"],
        "Kitchen": []  # Kitchen does not manage other roles
    }

    # Get all roles the creator can manage
    manageable_roles = role_hierarchy.get(creator_role, [])
    
    # Filter based on the target_role if provided
    if target_role and target_role not in manageable_roles:
        return []  # No notifications if the target role isn't manageable

    # Gather all users within manageable roles
    targets = []
    if creator_role == "Admin":  # Admin can see all
        targets += Admin.query.with_entities(Admin.id).all()
    if "Manager" in manageable_roles:
        targets += Manager.query.with_entities(Manager.id).all()
    if "SuperDistributor" in manageable_roles:
        targets += SuperDistributor.query.with_entities(SuperDistributor.id).all()
    if "Distributor" in manageable_roles:
        targets += Distributor.query.with_entities(Distributor.id).all()
    if "Kitchen" in manageable_roles:
        targets += Kitchen.query.with_entities(Kitchen.id).all()

    # Flatten list of tuples into a simple list of IDs
    return [t[0] for t in targets]

###################################### Create Notification ############################################
def create_notification(user_id, role, notification_type, description):
    notification = Notification(
        user_id=user_id,
        role=role,
        notification_type=notification_type,
        description=description,
        created_at=datetime.utcnow()
    )
    db.session.add(notification)
    db.session.commit()

    current_app.socketio.emit(
        'new_notification',
        {
            'user_id': user_id,
            'role': role,
            'notification_type': notification_type,
            'description': description,
            'timestamp': notification.created_at.isoformat(),
        },
        to='*/'
    )

    return notification

###################################### Check Notification #############################################
def check_notification(role, user_id):

    if role == 'Admin':
        notification_check = Notification.query.filter(
                    Notification.is_read == 0,
                ).all()
    else:    
        notification_check = Notification.query.filter(
                    Notification.user_id == user_id,
                    Notification.is_read == 0,
                    Notification.role == role
                ).all()  
    
    return notification_check

