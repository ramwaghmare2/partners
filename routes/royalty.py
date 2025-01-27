###################################### Importing Required Libraries ###################################
from flask import request, jsonify, Blueprint, render_template, redirect, url_for, session, flash
from utils.services import get_image, get_user_query, today_sale
from utils.notification_service import check_notification
from models.royalty import RoyaltySettings, RoyaltyWallet
from routes.user_routes import role_required
from datetime import datetime
from functools import wraps
from models import db

###################################### Blueprint For Royalty ######################################
royalty_bp = Blueprint('royalty', __name__, static_folder='../static')


###################################### Route for Add Royalty ######################################
@royalty_bp.route('/add-royalty', methods=['GET', 'POST'])
@role_required('Admin')
def add_royalty():
    
    role = session.get('role')
    user_id = session.get('user_id')
    image_data = get_image(role, user_id)
    user = get_user_query(role, user_id)

    share_percentages = RoyaltySettings.query.all()

    notification_check = check_notification(role, user_id)

    try:
        if request.method == 'POST':
            form_role = request.form.get('role')
            share = request.form.get('royalty')
            new_share = RoyaltySettings(
                role=form_role,
                royalty_percentage=share
            )
            db.session.add(new_share)
            db.session.commit()
            flash('Royalty Added Successfully', 'success')
            return redirect(url_for('royalty.add_royalty'))
    except Exception as e:
        flash(f'Error: {e}')
        return redirect(url_for('royalty.add_royalty'))
            

    return render_template('admin/royalty_sharing.html',
                           role=role,
                           encoded_image=image_data,
                           user_name=user.name,
                           shares=share_percentages,
                           notification_check=len(notification_check))


################################## Update Royalty Percentage (Admin-Only) ##################################
@royalty_bp.route('/update-royalty', methods=['POST'])
@role_required('Admin')
def update_royalty():
        
    if request.method == 'POST':
        data = request.form
        new_percentage = float(data.get("percentage"))
        if not new_percentage or not (0 < new_percentage <= 100):
            return jsonify({"error": "Invalid royalty percentage"}), 400

        setting = RoyaltySettings.query.filter_by(role=data.get('role')).first()
        if not setting:
            setting = RoyaltySettings(royalty_percentage=new_percentage)
            db.session.add(setting)
        else:
            setting.royalty_percentage = new_percentage

        db.session.commit()
        flash('Royalty Percentage Updated Successfully', 'success')
        return redirect(url_for('royalty.add_royalty'))


################################## Route for Distribute Royalty After Kitchen Close ##################################
@royalty_bp.route('/kitchen/close-day', methods=['POST'])
def close_day():
    data = request.json
    kitchen_id = data.get("kitchen_id")
    total_sales = data.get("total_sales")

    if not kitchen_id or not total_sales:
        return jsonify({"error": "Missing data"}), 400

    if total_sales < 1000:
        return jsonify({"message": "Sales did not reach the minimum threshold"}), 200

    setting = RoyaltySettings.query.first()
    if not setting:
        return jsonify({"error": "Royalty settings not found"}), 500

    royalty_percentage = setting.royalty_percentage
    royalty_per_entity = (total_sales * royalty_percentage / 20) / 4

    roles = ['Admin', 'Manager', 'Super Distributor', 'Distributor']
    for role in roles:
        wallet = RoyaltyWallet.query.filter_by(role=role).first()
        if not wallet:
            wallet = RoyaltyWallet(entity_id=None, role=role, royalty_amount=0.0)
            db.session.add(wallet)
        wallet.royalty_amount += royalty_per_entity
        wallet.updated_at = datetime.utcnow()

    db.session.commit()
    return jsonify({"message": "Royalty distributed successfully"})