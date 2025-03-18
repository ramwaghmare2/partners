from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db_mongo = client.chat_db

messages_collection = db_mongo.chat_messages
groups_collection = db_mongo.chat_groups
global_chat_collection = db_mongo.global_chat
users_collection = db_mongo.users