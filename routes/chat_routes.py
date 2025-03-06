import os
from utils.services import get_image, get_user_query
from utils.notification_service import check_notification
from werkzeug.utils import secure_filename
from flask import request, jsonify, Blueprint, current_app, render_template, session, redirect
from mdb_connection import messages_collection, global_chat_collection, groups_collection

chat_bp = Blueprint('chat_bp', __name__, static_folder='../static', template_folder='../templates')


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]

####################################### Fetch Private Messages ######################################
from bson import ObjectId

# Function to convert ObjectId to string
def objectid_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError("ObjectId is not serializable")

@chat_bp.route("/get_messages", methods=["GET"])
def get_messages():
    # Retrieve user session info
    user_id = session.get('user_id')
    role = session.get('role')
    
    if not user_id or not role:
        # Redirect or handle missing session data
        return redirect('/login')  # or some other error handling

    user_name = get_user_query(role, user_id)
    encoded_image = get_image(role, user_id)
    notification_check = check_notification(role, user_id)

    # Get query parameters
    sender_id = request.args.get("sender_id")
    receiver_id = request.args.get("receiver_id")
    page = int(request.args.get("page", 1))
    limit = 20
    last_timestamp = request.args.get('last_timestamp', None)

    # Validate sender and receiver IDs
    if not sender_id or not receiver_id:
        return "Invalid sender or receiver ID", 400

    try:
        # Attempt to convert sender_id and receiver_id to ObjectId
        sender_id = ObjectId(sender_id)
        receiver_id = ObjectId(receiver_id)
    except Exception as e:
        # If ObjectId conversion fails, return an error
        return f"Error converting sender_id or receiver_id to ObjectId: {str(e)}", 400

    # Create a query for the messages
    query = {
        "$or": [
            {"sender_id": sender_id, "receiver_id": receiver_id},
            {"sender_id": receiver_id, "receiver_id": sender_id},
        ]
    }
    if last_timestamp:
        query["timestamp"] = {"$lt": last_timestamp}

    # Fetch messages from MongoDB
    messages = messages_collection.find(query).sort("timestamp", -1).limit(limit)

    # Convert ObjectId to string for all messages
    result = []
    for msg in messages:
        msg["_id"] = objectid_to_str(msg["_id"])  # Convert ObjectId to string
        if "sender_id" in msg:
            msg["sender_id"] = objectid_to_str(msg["sender_id"])  # Convert sender_id to string
        if "receiver_id" in msg:
            msg["receiver_id"] = objectid_to_str(msg["receiver_id"])  # Convert receiver_id to string
        result.append(msg)

    # Render the template and pass necessary data
    return render_template('chats/get_messages.html', 
                           messages=result,
                           user_id=user_id,
                           role=role,
                           user_name=user_name.name,
                           encoded_image=encoded_image,
                           notification_check=len(notification_check)
                           )


####################################### Fetch Group Messages ######################################
@chat_bp.route("/get_group_messages", methods=["GET"])
def get_group_messages():
    group_id = request.args.get("group_id")

    messages = messages_collection.find({"group_id": group_id}).sort("timestamp", -1)

    return jsonify([msg for msg in messages])

####################################### Fetch Global Messages ######################################
@chat_bp.route("/get_global_messages", methods=["GET"])
def get_global_messages():
    messages = global_chat_collection.find().sort("timestamp", -1)
    return jsonify([msg for msg in messages])

####################################### File Uploade ######################################
@chat_bp.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file and "." in file.filename and file.filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]:
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        return jsonify({"file_url": file_path}), 200
    else:
        return jsonify({"error": "Invalid file type"}), 400