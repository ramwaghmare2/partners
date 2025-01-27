###################################### Importing Required Libraries ###################################
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from models import db, Notification
from utils.services import get_image, get_user_query
from utils.notification_service import check_notification
from datetime import datetime, timedelta

###################################### Blueprint For Notification #####################################
notification_bp = Blueprint('notification', __name__)

###################################### Route for Notifications ########################################
@notification_bp.route('/notifications', methods=['GET'])
def get_notifications():
    from models import Notification
    role = session.get('role')
    user_id = session.get('user_id')
    image_data = get_image(role, user_id)
    user = get_user_query(role, user_id)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if role == 'Admin':
        notifications = Notification.query.all()
    else:
        query = Notification.query

        if role:
            query = query.filter(Notification.role == role)
        if user_id:
            query = query.filter(Notification.user_id == user_id)
        if start_date:
            query = query.filter(Notification.created_at >= start_date)
        if end_date:
            query = query.filter(Notification.created_at <= end_date)

        notifications = query.order_by(Notification.created_at.desc()).all()

    notification_check = check_notification(role, user_id)

    today = datetime.today().date()
    yesterday = (datetime.today() - timedelta(days=1)).date()

    return render_template('notification.html',
                           role=role,
                           user_id=user_id,
                           encoded_image=image_data,
                           user_name=user.name,
                           notifications=notifications,
                           notification_check=len(notification_check),
                           today=today,
                           yesterday=yesterday
                           )

###################################### Route for Mark as Read ########################################
@notification_bp.route('/mark-as-read/<int:id>', methods=['GET'])
def mark_as_read(id):
    role = session.get('role')
    notification = Notification.query.get(id)
    try:
        if role == 'Admin' and notification:
            notification.is_read = True
            db.session.commit()
            return redirect(url_for('notification.get_notifications'))
        elif notification and session.get('user_id') == notification.user_id:
            notification.is_read = True
            db.session.commit()
            return redirect(url_for('notification.get_notifications'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('notification.get_notifications'))
    #     return jsonify({'message': 'Notification marked as read.'})
    # return jsonify({'error': 'Notification not found or unauthorized.'}), 404
    
###################################### Route for Delete Notifications #################################
@notification_bp.route('/notifications/delete', methods=['POST'])
def delete_notifications():
    user_id = request.json.get('user_id')
    Notification.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return jsonify({'message': 'Notifications deleted successfully.'})

