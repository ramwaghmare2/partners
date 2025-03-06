import os
from werkzeug.utils import secure_filename
from flask import request, jsonify, Blueprint, current_app
from mdb_connection import messages_collection

chat_bp = Blueprint('chat_bp', __name__, static_folder='../static')


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]

@chat_bp.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        return jsonify({"file_url": file_path}), 200
    else:
        return jsonify({"error": "Invalid file type"}), 400

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

    return jsonify([msg for msg in messages])
