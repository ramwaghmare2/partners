import os
from utils.services import get_image, get_user_query
from utils.notification_service import check_notification
from werkzeug.utils import secure_filename
from flask import request, jsonify, Blueprint, current_app, session, redirect, render_template
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


@chat_bp.route("/send_message", methods=["POST"])
def send_message():
    user_id = session.get('user_id')
    role = session.get('role')

    # Check if the user is authorized
    if not user_id or not role:
        return jsonify({"error": "Unauthorized"}), 401  

    data = request.get_json()
    sender_id = f"{role}-{user_id}"  
    receiver_id = data.get("receiver_id")
    message = data.get("message")

    # Ensure the receiver_id and message are present
    if not receiver_id or not message:
        return jsonify({"error": "Missing required fields"}), 400
    import pytz

    # Get the current UTC time
    utc_now = datetime.utcnow()

    # Define the IST timezone
    ist_timezone = pytz.timezone("Asia/Kolkata")

    # Convert UTC time to IST
    ist_now = pytz.utc.localize(utc_now).astimezone(ist_timezone)
    # Create the message data to insert
    message_data = {
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "message": encrypt_message(message),  # Encrypt the message before saving
        "timestamp": ist_now,
        "status": "sent"  # Status is 'sent' when it's first inserted
    }

    try:
        # Insert message into the database
        inserted_message = messages_collection.insert_one(message_data)

        # Return the message response with a decrypted message for display
        return jsonify({
            "message_id": str(inserted_message.inserted_id),
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "message": message,  # Send the original message (or send encrypted data if required)
            "timestamp": message_data["timestamp"],
            "status": "sent"
        }), 201

    except Exception as e:
        # Handle potential database errors
        return jsonify({"error": f"Failed to send message: {str(e)}"}), 500



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

    # Fetch user details (name, image, notifications)
    user_name = get_user_query(role, user_id)
    encoded_image = get_image(role, user_id)
    notification_check = check_notification(role, user_id)

    sender_id = request.args.get("sender_id")
    print(sender_id)
    receiver_id = request.args.get("receiver_id")
    page = int(request.args.get("page", 1))
    limit = 20

    # Query for total messages
    total_messages = messages_collection.count_documents(
        {
            "$or": [
                {"sender_id": sender_id, "receiver_id": receiver_id},
                {"sender_id": receiver_id, "receiver_id": sender_id},
            ]
        }
    )

    # Get the actual messages with pagination
    messages_cursor = messages_collection.find(
        {
            "$or": [
                {"sender_id": sender_id, "receiver_id": receiver_id},
                {"sender_id": receiver_id, "receiver_id": sender_id},
            ]
        }
    ).sort("timestamp", -1).skip((page - 1) * limit).limit(limit)

    messages = list(messages_cursor)
    print(messages)
    total_pages = (total_messages + limit - 1) // limit  # Calculate total pages

    # Collect unique users (sender and receiver) for batch query
    unique_users = set()
    for msg in messages:
        unique_users.add(msg.get("sender_id"))
        unique_users.add(msg.get("receiver_id"))

    # Batch query users to get their names
    connection = get_db_connection()
    try:
        from sqlalchemy import text
        placeholders = ", ".join([f"'{user}'" for user in unique_users])
        query = f"SELECT id, name FROM Admins WHERE id IN ({placeholders})"
        result = connection.execute(text(query)).fetchall()

        # Map user details by role and user_id
        user_details = {f"{row['role']}-{row['id']}": row['name'] for row in result}
        print(result)
    finally:
        connection.close()

    # Prepare messages with sender/receiver names
    messages_list = []
    for msg in messages:
        #sender_name = user_details.get(f"{msg['sender_id']}", "Unknown")
        #receiver_name = user_details.get(f"{msg['receiver_id']}", "Unknown")
        
        # Add the message data along with sender and receiver names
        messages_list.append({
            "message_id": objectid_to_str(msg["_id"]),
            #"sender_name": sender_name,
            #"receiver_name": receiver_name,
            "message": msg["message"],  # Ensure you decrypt the message if it's encrypted
            #"timestamp": msg["timestamp"]
        })
    # Render the template with messages and other data
    return render_template(
        'chats/get_messages.html',
        role=role,
        encoded_image=encoded_image,
        user_name=user_name.name,
        notification_check=len(notification_check),
        messages=messages_list,
        total_pages=total_pages,  # Pass total pages for pagination
        current_page=page  # Pass the current page number for frontend pagination control
    )



    # return jsonify({
    #     "total_messages": total_messages,
    #     "total_pages": total_pages,
    #     "current_page": page,
    #     "messages": messages_list
    # })



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
