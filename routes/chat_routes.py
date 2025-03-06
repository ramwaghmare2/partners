import os
from werkzeug.utils import secure_filename
from flask import request, jsonify, Blueprint, current_app
from mdb_connection import messages_collection, global_chat_collection, groups_collection

chat_bp = Blueprint('chat_bp', __name__, static_folder='../static')


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]

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

    return jsonify([msg for msg in messages])

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