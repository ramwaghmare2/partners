###################################### Importing Required Libraries ###################################
from flask import jsonify

###################################### Format Response ################################################
def format_response(status=200, message=None, data=None):
    response = {'status': status, 'message': message}
    if data:
        response['data'] = data
    return jsonify(response), status

###################################### Handle Error ###################################################
def handle_error(e):
    return format_response(status=500, message=str(e))


