###################################### Importing Required Libraries ###################################
from models import db
from flask import  request, jsonify, session, Blueprint
from flask_socketio import emit
from datetime import datetime, timezone
from app import socketio
from utils.services import ROLE_MODEL_MAP

###################################### Blueprint For User #############################################
user_bp = Blueprint('user_bp', __name__, static_folder='../static')


###################################### Handel Connect Disconnect ######################################
@socketio.on('connect')
def handle_connect():
    try:
        user_id = session.get('user_id')
        role = session.get('role')

        if user_id and role:
            # The globally defined role_model_map
            model = ROLE_MODEL_MAP(role)
            if model:
                user = model.query.get(user_id)
                if user:
                    user.online_status = True
                    user.last_seen = datetime.now(timezone.utc)
                    db.session.commit()

                    # Notify all connected clients
                    socketio.emit(
                        'status_update',
                        {'user_id': user.id, 
                         'status': 'online', 
                         'role': role,
                         'laste_seen': user.last_seen.isoformat()
                         },
                        broadcast=True
                    )
    except Exception as e:
        print(f"Error in handle_connect: {str(e)}")

###################################### Handel Disconnect ##############################################
@socketio.on('disconnect')
def handle_disconnect():
    reasone = request.args.get('reason', 'unknown')
    print(f"User disconnected due to:{reasone}")
    try:
        user_id = session.get('user_id')
        role = session.get('role')

        if user_id and role:
            model = ROLE_MODEL_MAP(role)
            if model:
                user = model.query.get(user_id)
                if user:
                    user.online_status = False
                    user.last_seen = datetime.now(timezone.utc)
                    db.session.commit()

                    socketio.emit(
                        'status_update',
                        {'user_id': user.id, 
                         'status': 'offline', 
                         'role': role,
                         'laste_seen': user.last_seen.isoformat()
                         },
                        broadcast=True
                    )
        else:
            print("Session data missing on disconnect.")
    except Exception as e:
        print(f"Error in handle_disconnect: {str(e)}")

###################################### Update User Status #############################################
@user_bp.route('/update-status', methods=['POST'])
def update_status():
    try:
        data = request.get_json()
        status = data.get('status')
        user_id = session.get('user_id')
        role = session.get('role')

        if user_id and role and status:
            model = ROLE_MODEL_MAP(role)
            if model:
                user = model.query.get(user_id)
                if user:
                    user.online_status = (status == 'online')
                    user.last_seen = datetime.now(timezone.utc)
                    db.session.commit()
        return jsonify({"message": "Status updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
