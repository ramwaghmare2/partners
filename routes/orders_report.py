###################################### Importing Required Libraries ###################################
from models import db, Manager, SuperDistributor, Distributor, Kitchen, Sales, Order, Customer, FoodItem
from flask import Blueprint, request, session, render_template
from utils.services import get_image, get_user_query
from datetime import datetime, timedelta
from utils.notification_service import check_notification
from collections import defaultdict
from models.order import OrderItem
from sqlalchemy import func ,desc
from .user_routes import role_required
from sqlalchemy import and_

###################################### Blueprint for Orders data Visualization API ####################
orders_bp = Blueprint('orders', __name__, url_prefix='/sales')

###################################### Orders data visualization API ##################################
@orders_bp.route('/list', methods=['GET'])
def order_list():
    role = session.get('role')
    user_id = session.get('user_id')
    user = get_user_query(role, user_id)
    encoded_image = get_image(role, user_id)
    search_query = request.args.get('search', '', type=str)
    filter_by = request.args.get('filter_by', 'all')
    order_status = request.args.get('status', '', type=str)

    query = Order.query
    total_quantity_query = None

    # Apply role-based filtering
    if role == 'Admin':
        query = query  # Admin sees all orders
        total_quantity_query = db.session.query(func.sum(OrderItem.quantity))
    
    elif role == 'Manager':
        # Manager's query scope and total quantity calculation
        total_quantity_query = db.session.query(func.sum(OrderItem.quantity)) \
                                         .join(Order, OrderItem.order_id == Order.order_id) \
                                         .join(Kitchen, Order.kitchen_id == Kitchen.id) \
                                         .join(Distributor, Kitchen.distributor_id == Distributor.id) \
                                         .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id) \
                                         .filter(SuperDistributor.manager_id == user_id)

        query = query.join(Kitchen, Order.kitchen_id == Kitchen.id) \
                     .join(Distributor, Kitchen.distributor_id == Distributor.id) \
                     .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id) \
                     .filter(SuperDistributor.manager_id == user_id)
        # Calculate total quantity sold
    total_quantity_sold = total_quantity_query.scalar() if total_quantity_query else 0
    

    # Apply search filters
    if search_query:
        if search_query.isdigit():
            if filter_by == 'user_id':
                query = query.filter(Order.user_id == int(search_query))
            elif filter_by == 'order_id':
                query = query.filter(Order.order_id == int(search_query))
            elif filter_by == 'kitchen_id':
                query = query.filter(Order.kitchen_id == int(search_query))
        else:
            query = query.join(Customer, Order.user_id == Customer.user_id) \
                         .filter(Customer.name.ilike(f'%{search_query}%'))

    # Clone the query for total count calculations
    total_query = query

    # Apply status filter for displaying orders
    if order_status:
        if order_status in ['pending', 'processing', 'cancelled', 'completed']:
            query = query.filter(Order.order_status == order_status)

    # Order by created_at
    query = query.order_by(Order.created_at.desc())
    orders = query.all()

    # Calculate overall order statistics (without status filter)
    total_order_count = total_query.count()
    
    total_completed_orders = total_query.filter(Order.order_status == 'completed').count()
    total_cancelled_orders = total_query.filter(Order.order_status == 'cancelled').count()
    total_pending_orders = total_query.filter(Order.order_status == 'pending').count()

    # Calculate displayed statistics
    displayed_order_ids = [order.order_id for order in orders]
    displayed_order_count = len(orders)
    displayed_quantity_sold = db.session.query(func.sum(OrderItem.quantity)) \
                                        .filter(OrderItem.order_id.in_(displayed_order_ids)) \
                                        .scalar() or 0

    return render_template('admin/order_list.html', 
                           orders=orders, 
                           exception_message=None,
                           total_order_count=total_order_count,
                           total_quantity_sold=total_quantity_sold,
                           total_completed_orders=total_completed_orders,
                           total_cancelled_orders=total_cancelled_orders,
                           total_pending_orders=total_pending_orders,
                           displayed_order_count=displayed_order_count,
                           user_name=user.name,
                           role=role,
                           encoded_image=encoded_image)
