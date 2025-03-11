import os
from utils.services import get_image, get_user_query
from utils.notification_service import check_notification
from werkzeug.utils import secure_filename
from flask import request, jsonify, Blueprint, current_app, session, redirect
from mdb_connection import messages_collection, global_chat_collection
from config import get_db_connection 
from mdb_connection import messages_collection, db_mongo
import uuid
from datetime import datetime
from routes.chat import encrypt_message, decrypt_message

chat_bp = Blueprint('chat_bp', __name__, static_folder='../static', template_folder='../templates')
messages_collection = db_mongo.chat_messages

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]

####################################### Fetch All Users for Chat ######################################
@chat_bp.route("/get_chat_users", methods=["GET"])
def get_chat_users():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        
        tables = {
            "Admin": "Admin",
            "Manager": "Manager",
            "Super Distributor": "Super_Distributor",
            "Distributor": "Distributor",
            "Kitchen": "Kitchen"
        }

        users_list = []

        for role, table in tables.items():
            query = f"SELECT id, name FROM {table}"
            cursor.execute(query)
            users = cursor.fetchall()

            for user in users:
                users_list.append({
                    "id": user["id"], 
                    "name": user["name"],
                    "role": role
                })

        cursor.close()
        connection.close()

        return jsonify({"status": "success", "users": users_list})
    
    finally:
        cursor.close()
        connection.close()
        

    #except Exception as e:
        #return jsonify({"status": "error", "message": str(e)})

####################################### Send Message routes ######################################
@chat_bp.route("/send_message", methods=["POST"])
def send_message():
    user_id = session.get('user_id')
    role = session.get('role')

    if not user_id or not role:
        return jsonify({"error": "Unauthorized"}), 401  

    data = request.get_json()
    sender_id = f"{role}-{user_id}"  
    receiver_id = data.get("receiver_id")
    message = data.get("message")

    if not receiver_id or not message:
        return jsonify({"error": "Missing required fields"}), 400

    message_data = {
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "message": encrypt_message(message),  
        "timestamp": datetime.utcnow(),
        "status": "sent"  
    }

    inserted_message = messages_collection.insert_one(message_data)

    return jsonify({
        "message_id": str(inserted_message.inserted_id),
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "message": message,
        "timestamp": message_data["timestamp"],
        "status": "sent"
    }), 201

####################################### Fetch Private Messages ######################################
from bson import ObjectId

def objectid_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError("ObjectId is not serializable")

@chat_bp.route("/get_messages", methods=["GET"])
def get_messages():
    user_id = session.get('user_id')
    role = session.get('role')
    
    if not user_id or not role:
        return redirect('/login')  

    user_name = get_user_query(role, user_id)
    encoded_image = get_image(role, user_id)
    notification_check = check_notification(role, user_id)

    sender_id = request.args.get("sender_id")
    receiver_id = request.args.get("receiver_id")
    page = int(request.args.get("page", 1))
    limit = 20

    total_messages = messages_collection.count_documents(
        {
            "$or": [
                {"sender_id": sender_id, "receiver_id": receiver_id},
                {"sender_id": receiver_id, "receiver_id": sender_id},
            ]
        }
    )

    messages_cursor = messages_collection.find(
        {
            "$or": [
                {"sender_id": sender_id, "receiver_id": receiver_id},
                {"sender_id": receiver_id, "receiver_id": sender_id},
            ]
        }
    ).sort("timestamp", -1).skip((page - 1) * limit).limit(limit)

<<<<<<< HEAD
    unique_users = set()
    for msg in messages:
        if "sender_id" in msg:
            unique_users.add(msg["sender_id"])
        if "receiver_id" in msg:
            unique_users.add(msg["receiver_id"])
    import pymysql
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    
    user_details = {}
    tables = {
        "Admin": "admins",
        "Manager": "managers",
        "Super Distributor": "super_distributors",
        "Distributor": "distributors",
        "Kitchen": "kitchens",
    }

    for user in unique_users:
        role, user_id = user.split("-")
        if role in tables:
            query = f"SELECT name FROM {tables[role]} WHERE id = {user_id}"
            cursor.execute(query)
            result = cursor.fetchone()
            if result:
                user_details[user] = result["name"]
            else:
                user_details[user] = "Unknown"

    cursor.close()
    connection.close()
    messages_list = []
    for msg in messages:
        messages_list.append({
            "message_id": objectid_to_str(msg["_id"]),
            "sender_id": objectid_to_str(msg["sender_id"]),
            "sender_id": user_details.get(msg["sender_id"], "Unknown"),
            "receiver_id": objectid_to_str(msg["receiver_id"]),
=======
    messages = list(messages_cursor)
    total_pages = (total_messages + limit - 1) // limit  # Calculate total pages
    
    unique_users = set()
    for msg in messages:
        if "sender_id" in msg and "receiver_id" in msg:
            unique_users.add(msg["sender_id"])
            unique_users.add(msg["receiver_id"])

    connection = get_db_connection()
    try:
        result = connection.execute("SELECT id, name FROM Admin")
        users = [dict(row) for row in result]
        
        user_details = {}
        tables = {
            "Admin": "admins",
            "Manager": "managers",
            "Super Distributor": "super_distributors",
            "Distributor": "distributors",
            "Kitchen": "kitchens",
        }

        for user in unique_users:
            role, user_id = user.split("-")
            if role in tables:
                query = f"SELECT name FROM {tables[role]} WHERE id = {user_id}"
                result = connection.execute(query, (user_id)).fetchone()
                user_details[user] = result["name"] if result else "Unknown"
    
    finally:
        connection.close()
    
    messages_list = []
    for msg in messages:
        messages_list.append({
            "message_id": str(msg["_id"]),
            "sender_id": msg["sender_id"],
            "sender_name": user_details.get(str(msg["sender_id"]), "Unknown"),
            "receiver_id": msg["receiver_id"],
>>>>>>> partners--018
            "receiver": user_details.get(str(msg["receiver_id"]), "Unknown"),
            "message": decrypt_message(msg["message"]) if msg.get("message") else None,
            "timestamp": msg["timestamp"]
        })

    return jsonify({
        "total_messages": total_messages,
        "total_pages": total_pages,
        "current_page": page,
        "messages": messages_list
    })

<<<<<<< HEAD
    return render_template('chats/get_messages.html')
=======
>>>>>>> partners--018


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

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    file_size = file.seek(0, os.SEEK_END)
    if file_size > 10 * 1024 * 1024:  
        return jsonify({"error": "File too large"}), 400

    file.seek(0)  
    filename = secure_filename(file.filename)
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    return jsonify({"file_url": file_path}), 200
    

####################################### Mark as Delivered & Read ######################################
@chat_bp.route("/mark_as_delivered", methods=["POST"])
def mark_as_delivered():
    data = request.get_json()
    message_id = data.get("message_id")

    if not message_id:
        return jsonify({"error": "Message ID required"}), 400

    messages_collection.update_one(
        {"_id": ObjectId(message_id)},
        {"$set": {"status": "delivered"}}
    )
    return jsonify({"message": "Message marked as delivered"}), 200

####################################### Mark as Read ######################################
@chat_bp.route("/mark_as_read", methods=["POST"])
def mark_as_read():
    data = request.get_json()
    message_id = data.get("message_id")

    if not message_id:
        return jsonify({"error": "Message ID required"}), 400

    result = messages_collection.update_one(
        {"_id": ObjectId(message_id)},
        {"$set": {"status": "read"}}
    )
    
    if result.modified_count == 0:
        return jsonify({"message": "Message marked as read"}), 200
