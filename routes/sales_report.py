###################################### Importing Required Libraries ###################################
from models import db, Manager, SuperDistributor, Distributor, Kitchen, Sales, Order, Customer, FoodItem, FoodItem 
from flask import Blueprint, request, session, render_template
from utils.services import get_image, get_user_query
from datetime import datetime, timedelta
from utils.notification_service import check_notification
from collections import defaultdict
from models.order import OrderItem
from sqlalchemy import func ,desc
from .user_routes import role_required
from sqlalchemy import and_
from utils.services import SalesReport
from flask_login import current_user
from sqlalchemy import func
from flask import jsonify


###################################### Blueprint for Sales Report #####################################
sales_bp = Blueprint('sales', __name__, static_folder='../static')

###################################### Sales Data Visualization #######################################
"""@sales_bp.route('/sales_report', methods=['GET'])
def sales_report():
    role = session.get('role')
    user_id = session.get('user_id')
    user = get_user_query(role, user_id)
    encoded_image = get_image(role, user_id)
    # Get the filter parameter from the query string
    filter_param = request.args.get('filter', 'today')  # Default to 'today' if no filter provided
    today = datetime.today()
    start_time, end_time = None, None
 
    total_sales_amount = 0
    total_orders_count = 0
    quantity_sold = 0
    sales_data = []
    sales_by_date_dict = defaultdict(float)
 
    # Define time ranges based on the filter
    if filter_param == 'today':
        start_time = datetime.combine(today, datetime.min.time())
        end_time = datetime.combine(today + timedelta(days=1), datetime.min.time())
    elif filter_param == 'yesterday':
        start_time = datetime.combine(today - timedelta(days=1), datetime.min.time())
        end_time = datetime.combine(today, datetime.min.time())
    elif filter_param == 'week':
        start_time = today - timedelta(days=today.weekday())
        end_time = start_time + timedelta(days=7)
    elif filter_param == 'month':
        start_time = datetime(today.year, today.month, 1)
        next_month = today.month % 12 + 1
        year = today.year + (today.month // 12)
        end_time = datetime(year, next_month, 1)
    elif filter_param == 'year':
        start_time = datetime(today.year, 1, 1)
        end_time = datetime(today.year + 1, 1, 1)
 
    # Use SQLAlchemy 'and_' for combining filters
    filter_conditions = []
    if start_time:
        filter_conditions.append(Sales.datetime >= start_time)
    if end_time:
        filter_conditions.append(Sales.datetime < end_time)
 
    # Admin Query total sales, orders, and quantity
    total_sales_amount_query = db.session.query(func.sum(Order.total_amount))
    if filter_conditions:
        total_sales_amount_query = total_sales_amount_query.filter(and_(*filter_conditions))
    total_sales_amount = total_sales_amount_query.scalar() or 0
 
    total_orders_count_query = db.session.query(func.count(OrderItem.order_id))
    if filter_conditions:
        total_orders_count_query = total_orders_count_query.filter(and_(*filter_conditions))
    total_orders_count = total_orders_count_query.scalar() or 0
 
    quantity_sold_query = db.session.query(func.sum(OrderItem.quantity))
    if filter_conditions:
        quantity_sold_query = quantity_sold_query.filter(and_(*filter_conditions))
    quantity_sold = quantity_sold_query.scalar() or 0
 
    # Manager Query total sales, orders, and quantity
    sales = SalesReport()
    manager_total_sales_amount = sales.cpunt_func(user_id)
    print("manager_total_sales_amount: ", manager_total_sales_amount)
    
    # Query sales data for the table
    sales_data_query = db.session.query(
        Sales.sale_id,
        Sales.datetime,
        FoodItem.item_name,
        func.sum(OrderItem.price).label("total_price"),
        func.sum(OrderItem.quantity).label("total_quantity"),
    ).join(OrderItem, Sales.item_id == OrderItem.item_id)\
     .join(FoodItem, OrderItem.item_id == FoodItem.id)
   
    if filter_conditions:
        sales_data_query = sales_data_query.filter(and_(*filter_conditions))
    sales_data_query = sales_data_query.group_by(Sales.sale_id, FoodItem.item_name, Sales.datetime)\
                                       .order_by(Sales.datetime.desc())
    sales_data = sales_data_query.all()
 
    sales_by_item_query = db.session.query(
        FoodItem.item_name,
        func.sum(OrderItem.quantity).label("total_quantity"),
        func.sum(OrderItem.price).label("total_sales")
    ).join(OrderItem, FoodItem.id == OrderItem.item_id)\
     .join(Order, OrderItem.order_id == Order.order_id)
   
    if filter_conditions:
        sales_by_item_query = sales_by_item_query.filter(and_(*filter_conditions))
    sales_by_item_query = sales_by_item_query.group_by(FoodItem.item_name).all()
 
    # Convert the sales_by_item query results to a JSON-serializable format
    sales_by_item_data = [
        {'item_name': row.item_name, 'total_quantity': row.total_quantity, 'total_sales': float(row.total_sales)}
        for row in sales_by_item_query
    ]
 
    # Query sales by date for the line chart
    sales_by_date_query = db.session.query(
        func.date(Sales.datetime).label('sale_date'),
        func.sum(Order.total_amount).label('total_sales')
    ).join(Order, Sales.order_id == Order.order_id)
    if filter_conditions:
        sales_by_date_query = sales_by_date_query.filter(and_(*filter_conditions))
    sales_by_date_query = sales_by_date_query.group_by(func.date(Sales.datetime)).all()
   
    # Convert sales_by_date data to JSON-serializable format
    sales_by_date = [
        {'sale_date': str(row.sale_date), 'total_sales': float(row.total_sales)}
        for row in sales_by_date_query
    ]
   
    # Process sales_by_date into a dictionary for charts
    sales_by_date_dict = {entry['sale_date']: entry['total_sales'] for entry in sales_by_date}
   
    # Prepare chart data
    dates = list(sales_by_date_dict.keys()) if sales_by_date_dict else ["No Data"]
    sales = list(sales_by_date_dict.values()) if sales_by_date_dict else [0]
   
    return render_template(
        'admin/sales_report.html',
        total_sales_amount=total_sales_amount,
        total_orders_count=total_orders_count,
        quantity_sold=quantity_sold,
        filter_param=filter_param,  # Pass filter to the template
        sales_data=sales_data,
        dates=dates,
        sales=sales,
        role=role,
        user_name=user.name,
        encoded_image=encoded_image,
        sales_by_date=sales_by_date,
        sales_by_date_dict=dict(sales_by_date_dict),
        sales_by_item_data=sales_by_item_data  # Pass the sales_by_item_data
    )

"""

@sales_bp.route('/sales_report', methods=['GET'])
def sales_report():
    role = session.get('role')  # Optional: Use current_user.role for Flask-Login
    user_id = session.get('user_id')  # Optional: Use current_user.id for Flask-Login
    user = get_user_query(role, user_id)
    encoded_image = get_image(role, user_id)

    # Filter parameter for date range
    filter_param = request.args.get('filter', 'today')  # Default to 'today'
    today = datetime.today()
    start_time, end_time = None, None

    # Define date range based on filter_param
    if filter_param == 'all':
        start_time, end_time = None, None
    elif filter_param == 'today':
        start_time = datetime(today.year, today.month, today.day)
        end_time = start_time + timedelta(days=1)
    elif filter_param == 'yesterday':
        start_time = datetime(today.year, today.month, today.day) - timedelta(days=1)
        end_time = start_time + timedelta(days=1)
    elif filter_param == 'week':
        start_time = today - timedelta(days=today.weekday())  # Start of the week
        end_time = start_time + timedelta(days=7)
    elif filter_param == 'month':
        start_time = datetime(today.year, today.month, 1)
        next_month = today.replace(day=28) + timedelta(days=4)
        end_time = next_month.replace(day=1)
    elif filter_param == 'year':
        start_time = datetime(today.year, 1, 1)
        end_time = datetime(today.year + 1, 1, 1)
    else:
        return jsonify({"error": "Invalid filter parameter"}), 400

    # Base query with aggregations, filtering by Sales model
    summary_query = db.session.query(
        func.count(func.distinct(Order.order_id)).label("total_orders_count"),
        func.coalesce(func.sum(OrderItem.quantity), 0).label("quantity_sold"),
        func.coalesce(func.sum(Order.total_amount), 0).label("total_sales_amount")
    ).join(Sales, Order.order_id == Sales.order_id) \
     .join(OrderItem, Order.order_id == OrderItem.order_id)

    # Detailed sales data query
    sales_data_query = db.session.query(
        Sales.sale_id.label("sale_id"),
        Order.created_at.label("sale_date"),
        FoodItem.item_name.label("item_name"),
        OrderItem.price,
        OrderItem.quantity
    ).join(Order, Sales.order_id == Order.order_id) \
     .join(OrderItem, Order.order_id == OrderItem.order_id) \
     .join(FoodItem, OrderItem.item_id == FoodItem.id)

    # Apply date range filter
    if start_time and end_time:
        summary_query = summary_query.filter(Order.created_at.between(start_time, end_time))
        sales_data_query = sales_data_query.filter(Order.created_at.between(start_time, end_time))

    # Role-based filtering
    if role == 'Admin':
        pass  # Admin sees all orders
    elif role == 'Manager':
        summary_query = (
            summary_query.join(Kitchen, Order.kitchen_id == Kitchen.id)
            .join(Distributor, Kitchen.distributor_id == Distributor.id)
            .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id)
            .filter(SuperDistributor.manager_id == user_id)
        )
        sales_data_query = (
            sales_data_query.join(Kitchen, Order.kitchen_id == Kitchen.id)
            .join(Distributor, Kitchen.distributor_id == Distributor.id)
            .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id)
            .filter(SuperDistributor.manager_id == user_id)
        )
    elif role == 'SuperDistributor':
        summary_query = (
            summary_query.join(Kitchen, Order.kitchen_id == Kitchen.id)
            .join(Distributor, Kitchen.distributor_id == Distributor.id)
            .filter(Distributor.super_distributor == user_id)
        )
        sales_data_query = (
            sales_data_query.join(Kitchen, Order.kitchen_id == Kitchen.id)
            .join(Distributor, Kitchen.distributor_id == Distributor.id)
            .filter(Distributor.super_distributor == user_id)
        )
    elif role == 'Distributor':
        summary_query = (
            summary_query.join(Kitchen, Order.kitchen_id == Kitchen.id)
            .filter(Kitchen.distributor_id == user_id)
        )
        sales_data_query = (
            sales_data_query.join(Kitchen, Order.kitchen_id == Kitchen.id)
            .filter(Kitchen.distributor_id == user_id)
        )
    elif role == 'Kitchen':
        summary_query = summary_query.filter(Order.kitchen_id == user_id)
        sales_data_query = sales_data_query.filter(Order.kitchen_id == user_id)

    # Execute the queries
    try:
        summary_data = summary_query.one_or_none()  # Fetch a single row
        sales_data = sales_data_query.all()  # Fetch all rows for sales data
    except Exception as e:
        print(f"Error during query execution: {e}")
        summary_data = (0, 0, 0)
        sales_data = []

    # Unpack the summary results
    total_orders_count, quantity_sold, total_sales_amount = summary_data or (0, 0, 0)

    # Prepare data for charts
    sales_by_date = defaultdict(float)
    sales_by_item = defaultdict(float)

    for sale in sales_data:
        sale_date = sale.sale_date.strftime('%Y-%m-%d')
        sale_amount = float(sale.price) * sale.quantity  # Convert Decimal to float
        sales_by_date[sale_date] += sale_amount
        sales_by_item[sale.item_name] += sale_amount

    # Convert defaultdicts to lists of dictionaries for easy JSON conversion
    sales_by_date_list = [{'date': date, 'total_sales': total} for date, total in sales_by_date.items()]
    sales_by_item_list = [{'item_name': item, 'total_sales': total} for item, total in sales_by_item.items()]

    # Return JSON data for JavaScript
    return render_template(
        'admin/sales_report.html',
        role=role,
        user_id=user_id,
        user_name=user.name,
        total_sales_amount=total_sales_amount or 0,
        total_orders_count=total_orders_count or 0,
        quantity_sold=quantity_sold or 0,
        user=user,
        encoded_image=encoded_image,
        filter_param=filter_param,
        sales_by_date_data=sales_by_date_list,  # Pass sales by date data
        sales_by_item_data=sales_by_item_list,  # Pass sales by item data
        sales_data=sales_data
    )