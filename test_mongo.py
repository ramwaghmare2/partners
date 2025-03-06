from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client.chat_db 

db.chat_messages.insert_one({"user": "test_user", "message": "Hello, MongoDB!"})

print("Inserted a test document into chat_messages collection!")
