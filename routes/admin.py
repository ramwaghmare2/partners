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

###################################### Admin Blueprint #######################################################
admin_bp = Blueprint('admin_bp', __name__, static_folder='../static')


###################################### Route for displaying admin dashboard ##################################
@admin_bp.route('/admin', methods=['GET'])
@role_required('Admin')
def admin_home():
    # Fetch session data
    role = session.get('role')
    user_id = session.get('user_id')
    user = get_user_query(role, user_id)
    encoded_image = get_image(role, user_id)

    # Initialize counts, totals, and sales data
    manager_count = 0
    super_distributor_count = 0
    distributor_count = 0
    kitchen_count = 0
    total_sales_amount = 0
    total_orders_count = 0
    quantity_sold = 0
    sales_data = []
    monthly_sales = []

    # Chart data initial values
    months = []
    total_sales = []
    kitchen_names = []
    order_counts = []
    pie_chart_labels = []
    pie_chart_data = []

    barChartData = {
        "labels": ["January", "February", "March", "April"],
        "values": [10, 20, 15, 30],
    }

    try:
        # Fetch counts
        manager_count = len(Manager.query.all())
        super_distributor_count = len(SuperDistributor.query.all())
        distributor_count = len(Distributor.query.all())
        kitchen_count = len(Kitchen.query.all())

        # Aggregate totals
                # Total sales amount from Orders where order_id is in Sales
        total_sales_amount = (
            db.session.query(func.sum(Order.total_amount))
            .join(Sales, Sales.order_id == Order.order_id)
            .scalar() or 0
        )

        # Total orders count where order_id is in Sales
        total_orders_count = (
            db.session.query(func.count(Order.order_id))
            .scalar() or 0
        )

        # Total quantity sold from OrderItems where order_id is in Sales
        quantity_sold = (
            db.session.query(func.sum(OrderItem.quantity))
            .join(Order, OrderItem.order_id == Order.order_id)
            .join(Sales, Sales.order_id == Order.order_id)
            .scalar() or 0
        )

        # Sales data
        sales_data = db.session.query(
            Sales.sale_id,
            Sales.datetime,
            FoodItem.item_name,
            OrderItem.price,
            OrderItem.quantity,
            Order.order_id
        ).join(Order, Sales.order_id == Order.order_id) \
        .join(OrderItem, Order.order_id == OrderItem.order_id) \
        .join(FoodItem, OrderItem.item_id == FoodItem.id) \
        .order_by(desc(Sales.sale_id))\
        .all()

    except Exception as e:
        print(f"Error fetching data: {e}")

    notification_check = check_notification(role, user_id)

    # Render the admin dashboard template
    return render_template(
        'admin/admin_index.html',
        manager_count=manager_count,
        super_distributor_count=super_distributor_count,
        distributor_count=distributor_count,
        kitchen_count=kitchen_count,
        total_sales_amount=total_sales_amount,
        total_orders_count=total_orders_count,
        quantity_sold=quantity_sold,
        sales_data=sales_data,
        user_name=user.name,
        notification_check=len(notification_check),
        role=role,
        months=months,
        total_sales=total_sales,
        barChartData=barChartData,
        encoded_image=encoded_image,
        kitchen_names=kitchen_names,
        order_counts=order_counts,
        pie_chart_labels=pie_chart_labels,
        pie_chart_data=pie_chart_data
    )


###################################### View Details ###################################################
@admin_bp.route('/view-details/<int:user_id>', methods=['GET'])
def view_details(user_id):
    id = session.get('user_id')
    role = session.get('role')
    user_name = get_user_query(role, id)
    encoded_image = get_image(role, id)
    notification_check = check_notification(role, user_id)


    # Fetch the user (manager)
    user = Manager.query.filter_by(id=user_id).first()
    
    # Get Super Distributors for the manager
    sd = SuperDistributor.query.filter(SuperDistributor.manager_id == user.id).all()
    sd_ids = [s.id for s in sd]
    
    # Get Distributors for the Super Distributors
    distributors = Distributor.query.filter(Distributor.super_distributor.in_(sd_ids)).all()
    distributor_ids = [distributor.id for distributor in distributors]
    
    # Get Kitchens for the Distributors
    kitchens = Kitchen.query.filter(Kitchen.distributor_id.in_(distributor_ids)).all()
    kitchen_ids = [kitchen.id for kitchen in kitchens]
    
    # Get Sales data for the Kitchens
    sales_k = Sales.query.filter(Sales.kitchen_id.in_(kitchen_ids)).all()

    # Extract all order_ids from the sales data
    order_ids = [sale.order_id for sale in sales_k]
    
    # Get Orders data based on the order_ids
    orders = Order.query.filter(Order.order_id.in_(order_ids)).all()

    # Helper function to calculate total sales for a given list of kitchens
    def calculate_total_sales(kitchens_list):
        total_sales = 0
        for kitchen in kitchens_list:
            # Find the sales corresponding to this kitchen
            kitchen_sales = [sale for sale in sales_k if sale.kitchen_id == kitchen.id]
            
            # Collect orders related to these sales
            kitchen_orders = [order for order in orders if order.order_id in [sale.order_id for sale in kitchen_sales]]
            
            # Sum the total amount of orders for this kitchen
            total_sales += sum(order.total_amount for order in kitchen_orders)
        return total_sales

    # Create super distributor data with sales included
    super_distributor_data = [
        {
            'super_distributor_name': super_distributor.name,
            'total_sales': calculate_total_sales(
                [kitchen for distributor in distributors if distributor.super_distributor == super_distributor.id
                    for kitchen in kitchens if kitchen.distributor_id == distributor.id]
            )
        }
        for super_distributor in sd
    ]

    # Create distributor data with sales included
    distributor_data = [
        {
            'distributor_name': distributor.name,
            'super_distributor_name': distributor.super_distributor_relation.name,
            'total_sales': calculate_total_sales(
                [kitchen for kitchen in kitchens if kitchen.distributor_id == distributor.id]
            )
        }
        for distributor in distributors
    ]

    # Create kitchen data with sales included
    kitchen_data = [
        {
            'kitchen_name': kitchen.name,
            'distributor_name': kitchen.distributors.name,
            'total_sales': calculate_total_sales([kitchen])
        }
        for kitchen in kitchens
    ]

    details = 'Manager'

    return render_template('view_details.html',
                           role=role,
                           user_name=user_name.name,
                           encoded_image=encoded_image,
                           user=user,
                           details=details,
                           super_distributors=super_distributor_data,
                           distributors=distributor_data,
                           kitchens=kitchen_data,
                           notification_check=len(notification_check)
                           )
