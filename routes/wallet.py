###################################### Importing Required Libraries ###################################
from models import db ,Kitchen, SuperDistributor ,Distributor,Manager,Admin
from utils.services import get_image, get_user_query, today_sale
from models.royalty import RoyaltySettings, RoyaltyWallet
from utils.notification_service import check_notification
from flask import Blueprint, render_template, session
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func

###################################### Blueprint For Wallet ###########################################
wallet_bp = Blueprint('wallet', __name__, static_folder='../static')

###################################### Route for View Wallet ##########################################
@wallet_bp.route('/view', methods=['GET'])
def view_wallet():
    session_role = session.get('role')
    user_id = session.get('user_id')
    image_data = get_image(session_role, user_id)
    user = get_user_query(session_role, user_id)
    notification_check = check_notification(session_role, user_id)

    wallet = RoyaltyWallet.query.filter_by(entity_id=user_id).first()
    # Step 5: Calculate the sum of the total_amount (royalty_amount) for the logged-in user's role
    total_royalty_amount = db.session.query(func.round(func.sum(RoyaltyWallet.royalty_amount), 2)) \
    .filter(RoyaltyWallet.entity_id == user_id, RoyaltyWallet.role == session_role) \
    .scalar() or 0.0

    today_total_sales = today_sale(user_id) or Decimal(0)

    # Step 2: Get royalty percentages for all roles
    roles = ['Admin', 'Manager', 'SuperDistributor', 'Distributor']
    royalty_percentages = db.session.query(
            RoyaltySettings.role, RoyaltySettings.royalty_percentage
    ).filter(RoyaltySettings.role.in_(roles)).all()

        # Convert query result to a dictionary for easier access
    royalty_dict = {role: 0 for role in roles}  # Default 0 for roles not in the database
    for role, percentage in royalty_percentages:
        royalty_dict[role] = percentage
    print(royalty_dict)

        # Step 3: Calculate each role's royalty and the total distributed amount
    role_shares = {}
    total_distributed = 0

    for role in roles:
        share = (today_total_sales * Decimal(royalty_dict[role])) / Decimal(100)
        role_shares[role] = share
        total_distributed += share

        # Step 4: Calculate the remaining amount for the kitchen's wallet
    remaining_wallet = today_total_sales - total_distributed

    # Retrieve related entities using foreign key relationships
    kitchen = Kitchen.query.filter_by(id=user_id).first()
    distributor = Distributor.query.filter_by(id=kitchen.distributor_id).first() if kitchen else None
    super_distributor = SuperDistributor.query.filter_by(id=distributor.super_distributor).first() if distributor else None
    manager = Manager.query.filter_by(id=super_distributor.manager_id).first() if super_distributor else None
    admin = Admin.query.first()  # Assuming a single admin

    # Combine names with shares
    role_shares_with_names = {
                                "Admin": {
                                    "id": admin.id if admin else None,
                                    "name": admin.name if admin else None,
                                    "share": float(role_shares['Admin']),
                                    "royalty_percentage": royalty_dict['Admin']
                                },
                                "Manager": {
                                    "id": manager.id if manager else None,
                                    "name": manager.name if manager else None,
                                    "share": float(role_shares['Manager']),
                                    "royalty_percentage": royalty_dict['Manager']
                                },
                                "SuperDistributor": {
                                    "id": super_distributor.id if super_distributor else None,
                                    "name": super_distributor.name if super_distributor else None,
                                    "share": float(role_shares['SuperDistributor']),
                                    "royalty_percentage": royalty_dict['SuperDistributor']
                                },
                                "Distributor": {
                                    "id": distributor.id if distributor else None,
                                    "name": distributor.name if distributor else None,
                                    "share": float(role_shares['Distributor']),
                                    "royalty_percentage": royalty_dict['Distributor']
                                },
                                "Kitchen": {
                                    "id": kitchen.id if kitchen else None,
                                    "name": kitchen.name if kitchen else None,
                                    "share": float(remaining_wallet),
                                    "royalty_percentage": None  # Kitchen does not have a royalty percentage
                                },
                            }   
    

    # Store calculated shares temporarily in the session
    session['role_shares'] = role_shares_with_names
    # Pass the data to the HTML template
    print('after', session_role)
    return render_template('kitchen/wallet.html',
                           encoded_image=image_data,
                           user_name=user.name,
                           user_id=user_id,
                           total_sales=today_total_sales,
                           role=session_role,
                           role_shares_with_names=role_shares_with_names,
                           remaining_wallet=remaining_wallet,
                           total_royalty_amount=total_royalty_amount,
                           notification_check=len(notification_check)
                           )


###################################### ROute for View All Wallets #####################################
@wallet_bp.route('/all', methods=['GET'])
def view_all_wallets():
    # Get the logged-in user's ID and role
    user_id = session.get('user_id')
    role = session.get('role')
    image_data = get_image(role, user_id)
    user = get_user_query(role, user_id)
    notification_check = check_notification(role, user_id)

    # Calculate total wallet amount for the user based on user_id and role
    total_wallet = db.session.query(func.sum(RoyaltyWallet.royalty_amount)) \
        .filter_by(entity_id=user_id, role=role).scalar() or 0.0

    # Round the total_wallet to 2 decimal places
    total_wallet = round(total_wallet, 2)

    # Calculate yesterday's wallet amount
    yesterday = datetime.utcnow() - timedelta(days=1)
    start_of_yesterday = datetime(yesterday.year, yesterday.month, yesterday.day)
    end_of_yesterday = start_of_yesterday + timedelta(days=1)

    yesterday_wallet = db.session.query(func.sum(RoyaltyWallet.royalty_amount)) \
        .filter(RoyaltyWallet.entity_id == user_id, RoyaltyWallet.role == role, 
                RoyaltyWallet.updated_at >= start_of_yesterday, RoyaltyWallet.updated_at < end_of_yesterday) \
        .scalar() or 0.0

    # Round the yesterday_wallet to 2 decimal places
    yesterday_wallet = round(yesterday_wallet, 2)

    daily_wallet = RoyaltyWallet.query.filter(RoyaltyWallet.role == role ,RoyaltyWallet.entity_id == user_id).all()
    print(daily_wallet)

    """wallet_data = {
                    "dates": [entry.updated_at.strftime('%Y-%m-%d') for entry in daily_wallet],
                    "amounts": [entry.royalty_amount for entry in daily_wallet]
                }"""    
    wallet_data = {
                "labels": [entry.updated_at.strftime('%Y-%m-%d') for entry in daily_wallet[-7:]],
                "values": [entry.royalty_amount for entry in daily_wallet[-7:]]
            }

    print(wallet_data)
    # Render the template and pass the data
    return render_template('wallet.html',
                           encoded_image=image_data,
                           user_name=user.name,
                           user_id=user_id,
                           role=role, 
                           total_wallet=total_wallet, 
                           yesterday_wallet=yesterday_wallet,
                           wallet_data=wallet_data,
                           notification_check=len(notification_check))
