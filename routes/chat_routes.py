from flask import Blueprint, request, render_template, session
from models import db, Admin, Manager, SuperDistributor, Distributor, Kitchen
from mdb_connection import personal_chat_collection, group_chat_collection, channel_collection ,messages_collection # Import collections
from flask import jsonify
from datetime import datetime
from bson import ObjectId
import time


# Initialize Blueprint
chat_bp = Blueprint('chat_bp', __name__, static_folder='../static', template_folder='../templates/chats')
@chat_bp.route('/landing', methods=['GET'])
def get_landing_page():
    try:
        # Get user ID and role from session
        user_id = session.get("user_id")
        user_role = session.get("role")
        print(user_role)

        if not user_id or not user_role:
            return "Unauthorized: User not logged in", 401

        # Identify user based on role
        role_model_map = {
            "admin": Admin,
            "manager": Manager,
            "super_distributor": SuperDistributor,
            "distributor": Distributor,
            "kitchen": Kitchen
        }

        user_model = role_model_map.get(user_role.lower())  # Fetch the correct model
        user = user_model.query.get(user_id) if user_model else None

        if not user:
            return "User not found", 404

        # Fetch chats where the logged-in user is the sender
        sender_chats = list(personal_chat_collection.find({
            "sender_id": user_id,
            "sender_role": {"$regex": f"^{user_role}$", "$options": "i"} 
        }))

        # Fetch chats where the logged-in user is the receiver
        receiver_chats = list(personal_chat_collection.find({
            "receiver_id": str(user_id),  # Convert user_id to string for matching
            "receiver_role": {"$regex": f"^{user_role}$", "$options": "i"}
        }))

        print(sender_chats, "sender_chats")  # Debugging output
        print(receiver_chats, "receiver_chats")  # Debugging output
        
        personal_chat_data = []

        # Process sender chats
        for chat in sender_chats:
            receiver_id = str(chat["receiver_id"])
            receiver_role = chat.get("receiver_role", "Unknown")

            # Fetch receiver's details from MySQL
            receiver_model = role_model_map.get(receiver_role.lower()) if receiver_role else None
            receiver = receiver_model.query.get(int(receiver_id)) if receiver_model and receiver_id.isdigit() else None
            receiver_name = receiver.name if receiver else "Unknown"

            # Prepare chat data
            last_message = chat["messages"][-1] if chat.get("messages") else {}
            personal_chat_data.append({
                "chat_id": str(chat["_id"]),
                "chat_type": "sent",  # Mark as sent chat
                "receiver_id": receiver_id,
                "receiver_name": receiver_name,
                "receiver_role": receiver_role,
                "last_message": last_message.get("text", ""),
                "timestamp": last_message.get("timestamp", None)
            })

        # Process receiver chats
        for chat in receiver_chats:
            sender_id = str(chat["sender_id"])
            sender_role = chat.get("sender_role", "Unknown")

            # Fetch sender details from MySQL
            sender_model = role_model_map.get(sender_role.lower()) if sender_role else None
            sender = sender_model.query.get(int(sender_id)) if sender_model and sender_id.isdigit() else None
            sender_name = sender.name if sender else "Unknown"

            # Prepare chat data
            last_message = chat["messages"][-1] if chat.get("messages") else {}
            timestamp = last_message.get("timestamp", None)

            personal_chat_data.append({
                "chat_id": str(chat["_id"]),
                "chat_type": "received",  # Mark as received chat
                "receiver_id": sender_id,  # Should be sender_id, not receiver_id
                "receiver_name": sender_name,  # Should be sender_name, not receiver_name
                "receiver_role": sender_role,
                "last_message": last_message.get("text", ""),
                "timestamp": timestamp if timestamp is not None else 0  # Handle None timestamps
            })

        return render_template(
            "chats/main_chat_page.html",
            user=user,
            personal_chats=personal_chat_data
        )

    except Exception as e:
        print("Error:", e)  # Debugging output
        return str(e), 500  


@chat_bp.route('/search_users', methods=['GET'])
def search_users():
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify([])

        user_id = session.get("user_id")  # Get the current logged-in user ID
        user_role = session.get("role")

        if not user_id or not user_role:
            return jsonify({"error": "Unauthorized"}), 401

        role_model_map = {
            "admin": Admin,
            "manager": Manager,
            "super_distributor": SuperDistributor,
            "distributor": Distributor,
            "kitchen": Kitchen
        }

        results = []
        for role, model in role_model_map.items():
            users = model.query.filter(model.name.ilike(f"%{query}%")).all()
            results.extend([
                {
                    "user_id": user.id,
                    "name": user.name,
                    "role": role.capitalize()
                } for user in users
            ])
            #print(results)

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat_bp.route('/start_chat', methods=['POST'])
def start_chat():
    try:
        data = request.get_json()
        receiver_id = data.get("receiver_id")
        receiver_role = data.get("role")  # Take receiver's role from frontend

        sender_id = session.get("user_id")
        sender_role = session.get("role")  # Fetch sender's role from session

        if not sender_id or not sender_role:
            return jsonify({"error": "Unauthorized"}), 401

        if not receiver_id or not receiver_role:
            return jsonify({"error": "Receiver ID and role are required"}), 400

        # Check if chat already exists
        existing_chat = personal_chat_collection.find_one({
            "$or": [
                {"sender_id": sender_id, "receiver_id": receiver_id},
                {"sender_id": receiver_id, "receiver_id": sender_id}
            ]
        })

        if existing_chat:
            return jsonify({
                "chat_id": str(existing_chat["_id"]),
                "receiver_id": receiver_id,
                "receiver_role": receiver_role,
                "name": data.get("name")
            })

        # Create new chat with sender and receiver roles
        new_chat = {
            "sender_id": sender_id,
            "sender_role": sender_role,
            "receiver_id": receiver_id,
            "receiver_role": receiver_role,  # Store receiver's role
            "messages": []
        }
        chat_id = personal_chat_collection.insert_one(new_chat).inserted_id

        return jsonify({
            "chat_id": str(chat_id),
            "receiver_id": receiver_id,
            "receiver_role": receiver_role,
            "name": data.get("name")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chat_bp.route('/send_message', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        receiver_id = str(data.get("receiver_id"))
        print('re_id',receiver_id)
        receiver_role = data.get("receiver_role")
        print("role",receiver_role)
        message_text = data.get("message")
        print('meassge_text',message_text)

        # Get user ID and role from session
        sender_id = session.get("user_id")
        sender_role = session.get("role")

        if not sender_id or not sender_role:
            return jsonify({"error": "Unauthorized: User not logged in"}), 401

        if not receiver_id or not message_text:
            return jsonify({"error": "Receiver ID and message are required"}), 400

        # Identify user model based on role
        role_model_map = {
            "admin": Admin,
            "manager": Manager,
            "super_distributor": SuperDistributor,
            "distributor": Distributor,
            "kitchen": Kitchen
        }

        sender_model = role_model_map.get(sender_role.lower())
        sender = sender_model.query.get(sender_id) if sender_model else None

        if not sender:
            return jsonify({"error": "Sender not found"}), 404

        # Check if the chat already exists
        existing_chat = personal_chat_collection.find_one({
            "$or": [
                {"sender_id": sender_id, "receiver_id": receiver_id},
                {"sender_id": receiver_id, "receiver_id": sender_id}
            ]
        })

        timestamp = int(time.time())  # Current timestamp in seconds

        if existing_chat:
            # Update existing chat with new message
            personal_chat_collection.update_one(
                {"_id": existing_chat["_id"]},
                {"$push": {"messages": {"text": message_text, "timestamp": timestamp}}}
            )
        else:
            # Create a new chat
            new_chat = {
                "sender_id": sender_id,
                "sender_role": sender_role,
                "receiver_id": receiver_id,
                "receiver_role": receiver_role,  # This should be updated later
                "messages": [{"text": message_text, "timestamp": timestamp}]
            }
            personal_chat_collection.insert_one(new_chat)

        return jsonify({"message": "Message sent successfully", "timestamp": timestamp}), 200

    except Exception as e:
        print("Error:", e)  # Debugging output
        return jsonify({"error": str(e)}), 500


        
@chat_bp.route('/fetch_messages/<receiver_id>', methods=['GET'])
def fetch_messages(receiver_id):
    try:
        # Get user ID and role from session
        sender_id = session.get("user_id")
        sender_role = session.get("role")

        if not sender_id or not sender_role:
            return jsonify({"error": "Unauthorized: User not logged in"}), 401

        # Fetch messages where logged-in user is either sender or receiver
        chat_cursor = personal_chat_collection.find({
            "$or": [
                {"sender_id": sender_id, "receiver_id": receiver_id},
                {"sender_id": receiver_id, "receiver_id": sender_id}
            ]
        })

        # Convert cursor to list of dictionaries
        chat_list = list(chat_cursor)

        # If no chat is found, return empty response
        if not chat_list:
            return jsonify({"messages": [], "chat_ids": []}), 200

        # Extract all messages from both sender and receiver documents
        all_messages = []
        for chat in chat_list:
            all_messages.extend(chat.get("messages", []))  # Merge messages
        print(all_messages)
        # Sort messages by timestamp
        all_messages.sort(key=lambda msg: msg.get("timestamp", 0))

        return jsonify({
            "chat_ids": [str(chat["_id"]) for chat in chat_list],  # Return all chat IDs
            "messages": all_messages
        }), 200

    except Exception as e:
        print("Error:", e)  # Debugging output
        return jsonify({"error": str(e)}), 500
