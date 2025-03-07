from flask import current_app
from flask_socketio import emit
from cryptography.fernet import Fernet
from datetime import datetime
from app import socketio
from mdb_connection import messages_collection, groups_collection, global_chat_collection
import uuid
import json

####################################### Generate AES Encryption Key (Run Once & Store Securely) ######################################
encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)

def encrypt_message(message):
    return cipher_suite.encrypt(message.encode()).decode()

def decrypt_message(encrypted_message):
    return cipher_suite.decrypt(encrypted_message.encode()).decode()


###################################### Private Chat (One-to-One Messaging) ###############################################
@socketio.on("private_message")
def handle_private_message(data):
    with current_app.app_context():
        sender_id = data["sender_id"]
        receiver_id = data["receiver_id"]
        message = encrypt_message(data.get("message", ""))  
        file_url = data.get("file_url", None)  
        file_type = data.get("file_type", None)  

        chat_message = {
            "_id": str(uuid.uuid4()),
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "message": message if message else None,  
            "file_url": file_url,  
            "file_type": file_type,
            "chat_type": "private",
            "status": "sent",
            "timestamp": datetime.utcnow(),
        }

        messages_collection.insert_one(chat_message)

        emit("receive_message", {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "message": data.get("message", ""),  
            "file_url": file_url,  
            "file_type": file_type,  
            "chat_type": "private"
        }, room=receiver_id)  


###################################### Group Chat (Users Can Create & Chat in Groups) ###################################### 
@socketio.on("create_group")
def create_group(data):
    group_name = data["group_name"]
    members = data["members"]  

    group = {
        "_id": str(uuid.uuid4()),
        "group_name": group_name,
        "members": members,
        "created_at": datetime.utcnow()
    }

    groups_collection.insert_one(group)
    emit("group_created", {"group_name": group_name, "group_id": group["_id"]}, broadcast=True)

@socketio.on("file_message")
def handle_file_message(data):
    sender_id = data["sender_id"]
    receiver_id = data["receiver_id"]
    file_url = data["file_url"]
    file_type = data["file_type"]

    chat_message = {
        "_id": str(uuid.uuid4()),
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "file_url": file_url,
        "file_type": file_type,
        "chat_type": "private",
        "status": "sent",
        "timestamp": datetime.utcnow(),
    }

    messages_collection.insert_one(chat_message)

    emit("receive_file", {
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "file_url": file_url,
        "file_type": file_type,
        "chat_type": "private"
    }, room=receiver_id)


@socketio.on("group_message")
def handle_group_message(data):
    sender_id = data["sender_id"]
    group_id = data["group_id"]
    message = encrypt_message(data["message"])
    file_url = data.get("file_url", None)  
    file_type = data.get("file_type", None) 

    chat_message = {
        "_id": str(uuid.uuid4()),
        "sender_id": sender_id,
        "group_id": group_id,
        "file_url": file_url,
        "file_type": file_type,
        "message": message,
        "chat_type": "group",
        "status": "sent",
        "timestamp": datetime.utcnow(),
    }

    messages_collection.insert_one(chat_message)

    group = groups_collection.find_one({"_id": group_id})
    if group:
        for member_id in group["members"]:
            emit("receive_message", {
                "sender_id": sender_id,
                "group_id": group_id,
                "message": data["message"],  
                "chat_type": "group"
            }, room=member_id)  


###################################### Global Chat (Messages Sent to All Users) ###################################### 
@socketio.on("global_message")
def handle_global_message(data):
    sender_id = data["sender_id"]
    message = encrypt_message(data["message"])

    global_chat = {
        "_id": str(uuid.uuid4()),
        "sender_id": sender_id,
        "message": message,
        "chat_type": "global",
        "timestamp": datetime.utcnow(),
    }

    global_chat_collection.insert_one(global_chat)

    emit("receive_message", {
        "sender_id": sender_id,
        "message": data["message"],  
        "chat_type": "global"
    }, broadcast=True)  

@socketio.on("message_delivered")
def message_delivered(data):
    message_id = data["message_id"]

    messages_collection.update_one(
        {"_id": message_id},
        {"$set": {"status": "delivered"}}
    )

    emit("message_status_update", {
        "message_id": message_id,
        "status": "delivered"
    }, broadcast=True)

@socketio.on("message_seen")
def message_seen(data):
    message_id = data["message_id"]

    messages_collection.update_one(
        {"_id": message_id},
        {"$set": {"status": "seen"}}
    )

    emit("message_status_update", {
        "message_id": message_id,
        "status": "seen"
    }, broadcast=True)

###################################### Flask WebSocket Signaling for WebRTC ########################################################3
@socketio.on("offer")
def handle_offer(data):
    receiver_id = data["receiver_id"]
    emit("receive_offer", data, room=receiver_id)

@socketio.on("answer")
def handle_answer(data):
    sender_id = data["sender_id"]
    emit("receive_answer", data, room=sender_id)

@socketio.on("ice_candidate")
def handle_ice_candidate(data):
    receiver_id = data["receiver_id"]
    emit("receive_ice_candidate", data, room=receiver_id)
