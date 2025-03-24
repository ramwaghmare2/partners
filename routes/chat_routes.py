from flask import Blueprint, request, render_template, session
from models import db, Admin, Manager, SuperDistributor, Distributor, Kitchen
from mdb_connection import personal_chat_collection, group_chat_collection, channel_collection ,messages_collection # Import collections
from flask import jsonify
from datetime import datetime
from bson import ObjectId
import time
import pytz
from utils.services import ROLE_MODEL_MAP


# Initialize Blueprint
chat_bp = Blueprint('chat_bp', __name__, static_folder='../static', template_folder='../templates/chats')



@chat_bp.route('/landing', methods=['GET'])
def get_landing_page():
    try:
        # Get user ID and role from session
        user_id = session.get("user_id")
        user_role = session.get("role")
        print("user_role",user_role)

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

        all_users = []
        for role, model in role_model_map.items():
            users = model.query.all()
            for u in users:
                all_users.append({
                    "id": u.id,  # Assuming `id` is the primary key
                    "name": u.name,  # Assuming `name` field exists
                    "role": role,
                    "contact":u.contact,
                    "email":u.email
                })


        if not user:
            return "User not found", 404

        user_mobile = user.contact  # Fetch mobile number

        # Fetch chats where the logged-in user is the sender
        sender_chats = list(personal_chat_collection.find({"sender_contact": user_mobile}))        

        # Fetch chats where the logged-in user is the receiver
        receiver_chats = list(personal_chat_collection.find({"receiver_contact": user_mobile}))
        #send_by_sender = [mesg for mesg in receiver_chats[0]["messages"] if user_mobile == mesg["sender_contact"] ]

        #print('sender',send_by_sender)
        # print(sender_chats, "sender_chats")  # Debugging output
        # print(receiver_chats, "receiver_chats")  # Debugging output

        personal_chat_data = []

        # Process sender chats
        for chat in sender_chats:
            receiver_mobile = chat["receiver_contact"]
            receiver_id = str(chat["receiver_id"])
            receiver_role = chat.get("receiver_role", "Unknown")

            # Fetch receiver's details using mobile number
            receiver = None
            for model in role_model_map.values():
                receiver = model.query.filter_by(contact=receiver_mobile).first()
                if receiver:
                    break  # Stop if user found

            receiver_name = receiver.name if receiver else "Unknown"

            # Prepare chat data
            last_message = chat.get("messages", [])[-1] if chat.get("messages") else {}

            personal_chat_data.append({
                "chat_id": str(chat["_id"]),
                "chat_type": "sent",  # Mark as sent chat
                "receiver_id": receiver_id,
                "receiver_role": receiver_role,
                "receiver_contact": receiver_mobile,
                "receiver_name": receiver_name,
                "last_message": last_message.get("text", ""),
                "timestamp": last_message.get("timestamp", None)
            })

        # Process receiver chats
        for chat in receiver_chats:
            sender_mobile = chat["sender_contact"]
            sender_id = str(chat["sender_id"])
            sender_role = chat.get("sender_role", "Unknown")

            # Fetch sender details using mobile number
            sender = None
            for model in role_model_map.values():
                sender = model.query.filter_by(contact=sender_mobile).first()
                if sender:
                    break  # Stop if user found

            sender_name = sender.name if sender else "Unknown"

            # Prepare chat data
            last_message = chat.get("messages", [])[-1] if chat.get("messages") else {}

            personal_chat_data.append({
                "chat_id": str(chat["_id"]),
                "chat_type": "received",  # Mark as received chat
                "receiver_id": sender_id,
                "receiver_role": sender_role,
                "receiver_contact": sender.contact,
                "receiver_name": sender.name,
                "last_message": last_message.get("text", ""),
                "timestamp": last_message.get("timestamp", None)
            })
        print(personal_chat_data)

        # Fetch groups where the user is a participant
        user_groups = list(group_chat_collection.find({
            "members": {
                "$elemMatch": {
                    "id": user_id,
                    "role": user_role,
                    "contact": user_mobile
                }
            }
        }))

        group_chat_data = []
        for group in user_groups:
            group_chat_data.append({
                "group_id": str(group["_id"]),
                "receiver_name": group["name"],
                "description": group.get("description", ""),
                "created_by": group["created_by"],
                "members": group["members"],
                "last_message": group.get("messages", [])[-1] if group.get("messages") else {},
            })
        print(group_chat_data)

        return render_template(
            "chats/main_chat_page.html",
            user=user,
            personal_chats=personal_chat_data,
            group_chats=group_chat_data,
            all_users=all_users
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
                    "user_contact": user.contact,
                    "name": user.name,
                    "role": role.capitalize()
                } for user in users
            ])
            # print(results)

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat_bp.route('/start_chat', methods=['POST'])
def start_chat():
    try:
        data = request.get_json()
        receiver_id = data.get("receiver_id")
        receiver_role = data.get("role")  # Take receiver's role from frontend
        print(f'Receiver_Role: {receiver_role}')
        receiver_model = ROLE_MODEL_MAP.get(receiver_role)
        receiver = receiver_model.query.filter_by(id=receiver_id).first()

        sender_id = session.get("user_id")
        sender_role = session.get("role")  # Fetch sender's role from session
        print(f'Sender_Role: {sender_role}')
        sender_model = ROLE_MODEL_MAP.get(sender_role)
        sender = sender_model.query.filter_by(id=sender_id).first()

        if not sender_id or not sender_role:
            return jsonify({"error": "Unauthorized"}), 401

        if not receiver_id or not receiver_role:
            return jsonify({"error": "Receiver ID and role are required"}), 400

        # Check if chat already exists
        existing_chat = personal_chat_collection.find_one({
            "$or": [
                {"sender_contact": sender.contact, "receiver_contact": receiver.contact},
                {"sender_contact": receiver.contact, "receiver_contact": sender.contact}
            ]
        })
        # print(existing_chat)
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
            "sender_contact": sender.contact,
            "receiver_id": receiver_id,
            "receiver_role": receiver_role,  # Store receiver's role
            "receiver_contact": receiver.contact,
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
        receiver_id = str(data.get("receiver_id"))  # Can be a user ID or group ID
        receiver_role = data.get("receiver_role")  # Null for group messages
        message_text = data.get("message")

        print(f"Received Data: receiver_id={receiver_id}, receiver_role={receiver_role}, message_text={message_text}")

        # Get user ID and role from session
        sender_id = session.get("user_id")
        sender_role = session.get("role")

        print(f"Session Data: sender_id={sender_id}, sender_role={sender_role}")

        if not sender_id or not sender_role:
            print("Unauthorized: User not logged in")
            return jsonify({"error": "Unauthorized: User not logged in"}), 401

        if not receiver_id or not message_text:
            print("Error: Receiver ID and message are required")
            return jsonify({"error": "Receiver ID and message are required"}), 400

        # Fetch sender details
        sender_model = ROLE_MODEL_MAP.get(sender_role)
        sender = sender_model.query.get(sender_id) if sender_model else None

        print(f"🔹 Sender Found: {sender}")

        if not sender:
            print("Error: Sender not found")
            return jsonify({"error": "Sender not found"}), 404

        timestamp = datetime.now(pytz.timezone('Asia/Kolkata'))  # Current timestamp

        # **Handle Group Chat**
        if ObjectId.is_valid(receiver_id):  
            print("Valid ObjectId detected, checking for group chat...")
            existing_group = group_chat_collection.find_one({"_id": ObjectId(receiver_id)})

            print(f"Group Chat Found: {existing_group}")

            if existing_group:
                # **Update Group Chat Messages**
                group_chat_collection.update_one(
                    {"_id": ObjectId(receiver_id)},
                    {"$push": {"messages": {
                        "text": message_text, 
                        "timestamp": timestamp, 
                        "sender_id": sender_id,
                        "sender_role": sender_role,
                        "sender_contact": sender.contact
                    }}}
                )
                print("Message added to group chat successfully")
                return jsonify({"message": "Message sent to group successfully", "timestamp": timestamp}), 200

        # **Handle Personal Chat**
        print("Checking for personal chat...")

        receiver_model = ROLE_MODEL_MAP.get(receiver_role)
        receiver = receiver_model.query.get(receiver_id) if receiver_model else None

        print(f"Receiver Found: {receiver}")

        if not receiver:
            print("Error: Receiver not found")
            return jsonify({"error": "Receiver not found"}), 404

        existing_chat = personal_chat_collection.find_one({
            "$or": [
                {"sender_contact": sender.contact, "receiver_contact": receiver.contact},
                {"sender_contact": receiver.contact, "receiver_contact": sender.contact}
            ]
        })

        print(f"Existing Personal Chat: {existing_chat}")

        if existing_chat:
            # Update existing chat
            personal_chat_collection.update_one(
                {"_id": existing_chat["_id"]},
                {"$push": {"messages": {"text": message_text, "timestamp": timestamp, "sender_contact": sender.contact}}}
            )
            print("Message added to existing personal chat")
        else:
            # Create new chat
            new_chat = {
                "sender_id": sender_id,
                "sender_role": sender_role,
                "sender_contact": sender.contact,
                "receiver_id": receiver_id,
                "receiver_role": receiver_role,
                "receiver_contact": receiver.contact,
                "messages": [{"text": message_text, "timestamp": timestamp}]
            }
            personal_chat_collection.insert_one(new_chat)
            print("New personal chat created and message added")

        return jsonify({"message": "Message sent successfully", "timestamp": timestamp}), 200

    except Exception as e:
        print("Error in send_message:", e)
        return jsonify({"error": str(e)}), 500

        


@chat_bp.route("/create_group", methods=["POST"])
def create_group():
    try:
        data = request.get_json()
        group_name = data.get("group_name")
        description = data.get("description")
        members = data.get("members")  # List of {"id": user_id, "mobile": contact_number, "role": user_role}
        print("members :", members)

        sender_id = session.get("user_id")
        sender_role = session.get("role").capitalize()  # Ensure sender's role is capitalized
        print("session data", sender_id, sender_role)

        if not sender_id or not sender_role:
            return jsonify({"error": "Unauthorized"}), 401

        if not group_name or not members:
            return jsonify({"error": "Group name and at least one member are required"}), 400

        sender_model = ROLE_MODEL_MAP.get(sender_role)
        sender = sender_model.query.filter_by(id=sender_id).first()
        
        if not sender:
            return jsonify({"error": "Sender not found"}), 404

        sender_contact = sender.contact  # Fetch sender's contact number
        print("sender_contact", sender_contact)

        # Retrieve receiver contact details
        member_contacts = []
        for member in members:
            member["role"] = member["role"].capitalize()  # Capitalize role first letter

            if member["id"] == sender_id and member["role"] == sender_role:
                # Skip adding the sender if they are already listed
                continue  

            member_model = ROLE_MODEL_MAP.get(member["role"])
            print("member_model", member_model)
            user = member_model.query.filter_by(id=member["id"]).first()
            print("user", user)
            if user:
                member_contacts.append({
                    "id": member["id"],
                    "role": member["role"],
                    "contact": member["mobile"]  # Use provided contact number
                })

        # Ensure sender is automatically included in the group
        member_contacts.append({"id": sender_id, "role": sender_role, "contact": sender_contact})
        print("member_contact_details", member_contacts)

        # Check if a group with the same members already exists
        existing_group = group_chat_collection.find_one({
            "members": {"$size": len(member_contacts), "$all": member_contacts}
        })

        if existing_group:
            return jsonify({
                "group_id": str(existing_group["_id"]),
                "name": existing_group["name"],
                "description": existing_group["description"],
                "members": existing_group["members"],
                "message": "Group already exists."
            })

        # Create new group
        new_group = {
            "name": group_name,
            "description": description,
            "created_by": {"id": sender_id, "role": sender_role, "contact": sender_contact},
            "members": member_contacts,
            "messages": [],
            # "created_at": datetime.utcnow()
        }

        group_id = group_chat_collection.insert_one(new_group).inserted_id

        return jsonify({
            "group_id": str(group_id),
            "name": group_name,
            "description": description,
            "members": member_contacts,
            "message": "Group created successfully."
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat_bp.route('/fetch_group_messages', methods=['GET'])
def fetch_group_messages():
    try:
        sender_id = session.get("user_id")
        sender_role = session.get("role")

        if not sender_id or not sender_role:
            return jsonify({"error": "Unauthorized: User not logged in"}), 401

        group_id = request.args.get("group_id")
        if not group_id:
            return jsonify({"error": "Invalid request. Provide group_id"}), 400

        group_chat = group_chat_collection.find_one({"_id": ObjectId(group_id)})

        if not group_chat:
            return jsonify({"error": "Group not found"}), 404

        member_contacts = [member["contact"] for member in group_chat.get("members", [])]
        sender_model = ROLE_MODEL_MAP.get(sender_role)
        sender = sender_model.query.get(sender_id) if sender_model else None

        if not sender or sender.contact not in member_contacts:
            return jsonify({"error": "Unauthorized: Not a member of this group"}), 403

        all_messages = group_chat.get("messages", [])
        all_messages.sort(key=lambda msg: msg.get("timestamp", 0))

        formatted_messages = [{
            "text": msg.get("text"),
            "timestamp": msg.get("timestamp"),
            "sender_name": msg.get("sender_name")
        } for msg in all_messages]

        return jsonify({
            "group_id": str(group_chat["_id"]),
            "messages": formatted_messages
        }), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500
    

@chat_bp.route('/fetch_personal_messages', methods=['GET'])
def fetch_personal_messages():
    try:
        sender_id = session.get("user_id")
        sender_role = session.get("role")

        if not sender_id or not sender_role:
            return jsonify({"error": "Unauthorized: User not logged in"}), 401

        receiver_id = request.args.get("id")
        receiver_role = request.args.get("role")

        if not receiver_id or not receiver_role:
            return jsonify({"error": "Invalid request. Provide receiver_id and receiver_role"}), 400

        sender_model = ROLE_MODEL_MAP.get(sender_role)
        sender = sender_model.query.get(sender_id) if sender_model else None
        receiver_model = ROLE_MODEL_MAP.get(receiver_role)
        receiver = receiver_model.query.get(receiver_id) if receiver_model else None

        if not sender or not receiver:
            return jsonify({"error": "Sender or Receiver not found"}), 404

        chat_cursor = personal_chat_collection.find({
            "$or": [
                {"sender_contact": sender.contact, "receiver_contact": receiver.contact},
                {"sender_contact": receiver.contact, "receiver_contact": sender.contact}
            ]
        })

        chat_list = list(chat_cursor)
        all_messages = [msg for chat in chat_list for msg in chat.get("messages", [])]
        all_messages.sort(key=lambda msg: msg.get("timestamp", 0))

        formatted_messages = [{
            "text": msg.get("text"),
            "timestamp": msg.get("timestamp"),
            "sender_name": msg.get("sender_name")
        } for msg in all_messages]

        return jsonify({
            "chat_ids": [str(chat["_id"]) for chat in chat_list],
            "messages": formatted_messages
        }), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500