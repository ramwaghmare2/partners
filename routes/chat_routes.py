from flask import Blueprint, request, render_template, session, jsonify
from models import db, Admin, Manager, SuperDistributor, Distributor, Kitchen
from mdb_connection import personal_chat_collection, group_chat_collection
from datetime import datetime
from bson import ObjectId
import traceback
from pymongo.errors import PyMongoError
import time
import pytz
import base64
from bson import Binary
from io import BytesIO
from utils.services import ROLE_MODEL_MAP, get_image


# Initialize Blueprint
chat_bp = Blueprint('chat_bp', __name__, static_folder='../static', template_folder='../templates/chats')


# Get current time in IST (Indian Standard Time)
timestamp_ist = datetime.now(pytz.timezone('Asia/Kolkata'))

# Format in 12-hour format with AM/PM
formatted_timestamp = timestamp_ist.strftime("%I:%M:%S %p")

@chat_bp.route('/landing', methods=['GET'])
def get_landing_page():
    try:
        # Get user ID and role from session
        user_id = session.get("user_id")
        user_role = session.get("role")
        encoded_image = get_image(user_role, user_id)

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

        user_model = ROLE_MODEL_MAP.get(user_role)  # Fetch the correct model
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

        # Mark all the messages as 'received' for the logged-in user
        personal_chats = list(personal_chat_collection.find({"$or": [{"sender_contact": user_mobile}, {"receiver_contact": user_mobile}]}))
        
        for chat in personal_chats:
            for msg in chat.get("messages", []):
                if msg.get("receiver_contact") == user_mobile and msg.get("status") != "received":
                    msg["status"] = "received"
            
            # Update the chat with the modified messages
            personal_chat_collection.update_one({"_id": chat["_id"]}, {"$set": {"messages": chat["messages"]}})

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
                    "id": str(user_id),
                    "role": user_role,
                    "contact": user_mobile
                }
            }
        }))
        group_chat_data = []
        for group in user_groups:
            group_image_binary = group.get("group_photo")  # Fetch the binary data for the image

            if group_image_binary:
                # Convert the binary image to a base64 string
                group_image_base64 = base64.b64encode(group_image_binary).decode('utf-8')
                group["group_photo"] = f"data:image/jpeg;base64,{group_image_base64}"  # Format for embedding in img tag
                
            else:
                group["group_photo"] = None  # If no image, set it to None

            group_chat_data.append({
                "group_id": str(group["_id"]),
                "receiver_name": group["name"],
                "description": group.get("description", ""),
                "created_by": group["created_by"],
                "members": group["members"],
                "last_message": group.get("messages", [])[-1] if group.get("messages") else {},
                "group_photo": group.get("group_photo")  # Pass the Base64 string for the image
            })

        return render_template(
            "chats/main_chat_page.html",
            user=user,
            role=user_role,
            personal_chats=personal_chat_data,
            group_chats=group_chat_data,
            all_users=all_users,
            image=encoded_image
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
        print(f'data {data}')
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

        timestamp = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%d-%m-%Y %I:%M:%S %p")

        print("timestamp", timestamp)

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
                        "status": "sent",  # Adding status to message
                        "sender_id": sender_id,
                        "sender_role": sender_role,
                        "sender_name": sender.name,
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
                {"_id": existing_chat["_id"]},  # Filter condition
                {  
                    "$push": {
                        "messages": {
                            "text": message_text, 
                            "timestamp": timestamp,
                            "status": "sent",  # Adding status to message
                            "sender_contact": sender.contact
                        }
                    }
                }
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
                "messages": [{
                    "text": message_text, 
                    "timestamp": timestamp,
                    "status": "sent"  # Adding status to message
                }],
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
        group_photo = data.get("group_photo")  # Base64 encoded image data (if provided)

        sender_id = session.get("user_id")
        sender_role = session.get("role").capitalize()

        if not sender_id or not sender_role:
            return jsonify({"error": "Unauthorized"}), 401

        if not group_name or not members:
            return jsonify({"error": "Group name and at least one member are required"}), 400

        sender_model = ROLE_MODEL_MAP.get(sender_role)
        sender = sender_model.query.filter_by(id=sender_id).first()

        if not sender:
            return jsonify({"error": "Sender not found"}), 404

        sender_contact = sender.contact

        # Prepare member contacts
        member_contacts = []
        for member in members:
            member["role"] = member["role"].replace("_", " ").title().replace(" ", "")
            if member["id"] == sender_id and member["role"] == sender_role:
                continue  

            member_model = ROLE_MODEL_MAP.get(member["role"])
            user = member_model.query.filter_by(id=member["id"]).first()
            if user:
                member_contacts.append({
                    "id": member["id"],
                    "role": member["role"],
                    "contact": member["mobile"]
                })

        # Ensure sender is automatically included in the group
        member_contacts.append({"id": sender_id, "role": sender_role, "contact": sender_contact})

        # Check if group already exists
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

        # Prepare the group document
        group_data = {
            "name": group_name,
            "description": description,
            "created_by": {"id": sender_id, "role": sender_role, "contact": sender_contact},
            "members": member_contacts,
            "messages": [],
        }

        # If an image is provided and is smaller than 10MB, store it directly in the document
        if group_photo:
            # Decode the base64 image
            image_data = base64.b64decode(group_photo.split(",")[1])  # Remove the "data:image/png;base64," part
            if len(image_data) < 10 * 1024 * 1024:  # Check if it's less than 10MB
                group_data["group_photo"] = Binary(image_data)  # Store image as binary

        # Create the group document
        group_id = group_chat_collection.insert_one(group_data).inserted_id

        return jsonify({
            "group_id": str(group_id),
            "name": group_name,
            "description": description,
            "members": member_contacts,
            "message": "Group created successfully."
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@chat_bp.route('/get_group_details', methods=['GET'])
def get_group_details():
    group_id = request.args.get('group_id')

    # Validate group_id format (MongoDB ObjectId)
    if not ObjectId.is_valid(group_id):
        return jsonify({"error": "Invalid group ID format"}), 400

    # Fetch group details from MongoDB
    group = group_chat_collection.find_one({"_id": ObjectId(group_id)})

    if not group:
        return jsonify({"error": "Group not found"}), 404

    # Process members
    members_data = []
    for member in group.get("members", []):
        member_id = member.get("id")
        role = member.get("role")
        contact = member.get("contact")

        # Fetch name from the respective SQLAlchemy model
        member_name = "Unknown"  # Default name if not found
        if role in ROLE_MODEL_MAP:
            model = ROLE_MODEL_MAP[role]
            member_obj = db.session.query(model).filter_by(id=member_id).first()
            if member_obj:
                member_name = member_obj.name  # Assuming all models have a 'name' column

        # Append member details
        members_data.append({
            "id": member_id,
            "name": member_name,
            "role": role,
            "contact": contact
        })
        print(members_data)
    return jsonify({
        "name": group.get("name", "No Name"),
        "description": group.get("description", "No Description"),
        "members": members_data
    })


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
        group_image_binary = group_chat.get("group_photo")  # Fetch the binary data for the image

        if group_image_binary:
            # Convert the binary image to a base64 string
            group_image_base64 = base64.b64encode(group_image_binary).decode('utf-8')
            group_chat["group_photo"] = f"data:image/jpeg;base64,{group_image_base64}"  # Format for embedding in img tag
            
        else:
            group_chat["group_photo"] = None  # If no image, set it to None

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
            "sender_name": msg.get("sender_name"),
            "sender_contact": msg.get("sender_contact")  # Include sender_contact
        } for msg in all_messages]

        return jsonify({
            "group_id": str(group_chat["_id"]),
            "messages": formatted_messages,
            "sender_contact": sender.contact if sender else None  # Send logged-in user's contact
        }), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500
    


@chat_bp.route('/remove_message/<string:group_id>', methods=['DELETE'])
def remove_message(group_id):
    try:
        # Get data from the request
        message_timestamp = request.json.get('timestamp')
        
        if not message_timestamp:
            return jsonify({"error": "Timestamp is required"}), 400
        
        # Check if the group_id is valid
        if not ObjectId.is_valid(group_id):
            return jsonify({"error": "Invalid group ID"}), 400
        
        # Remove message from the group's messages
        result = group_chat_collection.update_one(
            {'_id': ObjectId(group_id)}, 
            {'$pull': {'messages': {'timestamp': message_timestamp}}}
        )
        
        if result.modified_count > 0:
            return jsonify({"message": "Message removed successfully"}), 200
        else:
            return jsonify({"error": "Failed to remove message, message may not exist"}), 400
    
    except PyMongoError as e:
        # Handle any MongoDB-related errors
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        # Catch any other unexpected errors
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

    

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

        # Mark messages as "read" if they are delivered and the current user is the receiver
        for chat in chat_list:
            for msg in chat.get("messages", []):
                if msg.get("status") == "delivered" and msg.get("receiver_contact") == sender.contact:
                    msg["status"] = "read"  # Mark as read if receiver views it

            # Update the chat with modified messages
            personal_chat_collection.update_one({"_id": chat["_id"]}, {"$set": {"messages": chat["messages"]}})

        formatted_messages = [{
            "text": msg.get("text"),
            "timestamp": msg.get("timestamp"),
            "sender_name": msg.get("sender_name"),
            "sender_contact": msg.get("sender_contact"),
            "status": msg.get("status")
        } for msg in all_messages]

        return jsonify({
            "chat_ids": [str(chat["_id"]) for chat in chat_list],
            "messages": formatted_messages
        }), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500




@chat_bp.route('/get_available_users/<string:group_id>', methods=['GET'])
def get_available_users(group_id):
    try:
        # Validate group_id
        if not ObjectId.is_valid(group_id):
            return jsonify({"error": "Invalid group ID"}), 400

        # Fetch existing members from MongoDB
        group = group_chat_collection.find_one({"_id": ObjectId(group_id)}, {"members.id": 1})
        existing_member_ids = {member["id"] for member in group["members"]} if group and "members" in group else set()

        available_users = []  # Store users from all roles

        # Loop through role-based models and fetch users who are NOT in the group
        for role, model in ROLE_MODEL_MAP.items():
            users = db.session.query(model.id, model.name, model.email, model.contact).filter(
                ~model.id.in_(existing_member_ids)  # Exclude already added users
            ).all()

            # Append user data to list
            available_users.extend([
                {"id": str(user.id), "name": user.name, "email": user.email, "contact": user.contact, "role": role}
                for user in users
            ])

        return jsonify({"users": available_users}), 200

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@chat_bp.route('/update_group', methods=['POST'])
def update_group():
    try:
        data = request.json
        group_id = data.get("group_id")
        group_name = data.get("group_name")
        group_description = data.get("group_description")
        new_members = data.get("new_members", [])
        removed_members = data.get("removed_members", [])

        if not group_id:
            return jsonify({"error": "Group ID is required"}), 400

        update_query = {}
        if group_name:
            update_query["name"] = group_name
        if group_description:
            update_query["description"] = group_description

        update_operation = {"$set": update_query}

        if new_members:
            update_operation["$push"] = {"members": {"$each": new_members}}
        if removed_members:
            update_operation["$pull"] = {"members": {"id": {"$in": removed_members}}}

        result = group_chat_collection.update_one({"_id": ObjectId(group_id)}, update_operation)

        if result.modified_count == 0:
            return jsonify({"error": "No changes made"}), 200

        return jsonify({"message": "Group updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
