import os
from werkzeug.utils import secure_filename
from flask import request, jsonify, Blueprint, current_app
from mdb_connection import messages_collection, global_chat_collection, groups_collection
from flask import request, jsonify, Blueprint
from config import get_db_connection 
from mdb_connection import messages_collection, db_mongo
import uuid
from datetime import datetime
from routes.chat import decrypt_message

chat_bp = Blueprint('chat_bp', __name__, static_folder='../static')
messages_collection = db_mongo.chat_messages

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]

chat_bp = Blueprint("chat_bp", __name__)

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

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


####################################### Fetch Private Messages ######################################
@chat_bp.route("/get_messages", methods=["GET"])
def get_messages():
    sender_id = request.args.get("sender_id")
    receiver_id = request.args.get("receiver_id")
    page = int(request.args.get("page", 1))
    limit = 20

    messages = messages_collection.find(
        {
            "$or": [
                {"sender_id": sender_id, "receiver_id": receiver_id},
                {"sender_id": receiver_id, "receiver_id": sender_id},
            ]
        }
    ).sort("timestamp", -1).skip((page - 1) * limit).limit(limit)

    
    unique_users = set()
    for msg in messages:
        unique_users.add(msg["sender_id"])
        unique_users.add(msg["receiver_id"])

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
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
            "message_id": msg["_id"],
            "sender_id": msg["sender_id"],
            "sender_id": user_details.get(msg["sender_id"], "Unknown"),
            "receiver_id": msg["receiver_id"],
            "receiver": user_details.get(str(msg["receiver_id"]), "Unknown"),
            "message": decrypt_message(msg["message"]) if msg.get("message") else None,
            "timestamp": msg["timestamp"]
            
        })


    return jsonify(messages_list)


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