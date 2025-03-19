from pymongo import MongoClient

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
mongo_db = client["chat_db"]  # Change this to your actual database name

# Collections
personal_chat_collection = mongo_db["personal_chats"]
group_chat_collection = mongo_db["group_chats"]
channel_collection = mongo_db["channels"]
messages_collection = mongo_db["messages"]