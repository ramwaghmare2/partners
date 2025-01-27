###################################### Importing Required Libraries ###################################
from models import db, Manager, SuperDistributor, Distributor, Kitchen, Sales, Order, FoodItem
from flask import Blueprint, request, session, render_template
from utils.services import get_image, get_user_query, ROLE_MODEL_MAP
from utils.notification_service import check_notification
from datetime import datetime, timedelta, timezone
from models.order import OrderItem
from .admin import role_required
from flask_socketio import emit
from sqlalchemy import func

###################################### Blueprint Configuration ########################################
dashboard_bp = Blueprint('dashboard', __name__, static_folder='../static')

###################################### Route for displaying admin dashboard ###########################
@dashboard_bp.route('/admin', methods=['GET'])
@role_required('Admin')
def admin_dashboard():
    # Fetch session data
    role = session.get('role')
    user_id = session.get('user_id')
    user = get_user_query(role, user_id)
    encoded_image = get_image(role, user_id)

    # Initialize counts, totals, and sales data
    total_sales_amount, total_orders_count, quantity_sold = 0, 0, 0
    manager_total_sales_amount = 0
    sales_data = []
    notification_check = []
    #sales_distribution = []
    sales_by_item = {"labels": [], "values": []}
    quantity_sold_over_time = {"labels": [], "values": []}
    top_item_names, top_item_quantities = [], []
    distribution_labels, distribution_values = [], []
    performance_dates, total_revenues = [], []
    months, total_sales, kitchen_names, order_counts = [], [], [], []
    barChartData = {"labels": ["January", "February", "March", "April"], "values": [10, 20, 15, 30]}

    try:
        filter_type = request.args.get('filter', 'manager')
        # Aggregate totals
        total_sales_amount = db.session.query(func.sum(Order.total_amount)).scalar() or 0
        total_orders_count = OrderItem.query.count()
        quantity_sold = db.session.query(func.sum(OrderItem.quantity)).scalar() or 0
        
        manager_total_sales_amount = (
            db.session.query(db.func.sum(Order.total_amount))  
            .join(Kitchen, Order.kitchen_id == Kitchen.id)  
            .join(Distributor, Kitchen.distributor_id == Distributor.id)  
            .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id)  
            .filter(SuperDistributor.manager_id)  
            .scalar() or 0 
        )
        print("manager_total_sales_amount: ", manager_total_sales_amount)
        # Sales data
        sales_data = db.session.query(
            Sales.sale_id,
            Sales.datetime,
            FoodItem.item_name,
            func.sum(OrderItem.price).label("total_price"),
            func.sum(OrderItem.quantity).label("total_quantity")
        ).join(OrderItem, Sales.item_id == OrderItem.item_id)\
        .join(FoodItem, OrderItem.item_id == FoodItem.id)\
        .group_by(Sales.sale_id, FoodItem.item_name, Sales.datetime)\
        .order_by(Sales.datetime.desc())\
        .all()

        #Chart 1: Total Sales
        sales_by_manager_query = db.session.query(
            Manager.name.label("manager_name"),  # Replace with appropriate Manager field
            func.sum(Order.total_amount).label("total_sales")  # Sum of total_amount from Order table
        ).join(SuperDistributor, Manager.id == SuperDistributor.manager_id).join(Distributor, SuperDistributor.id == Distributor.super_distributor).join(Kitchen, Distributor.id == Kitchen.distributor_id).join(Order, Kitchen.id == Order.kitchen_id).join(Sales, Sales.order_id == Order.order_id).group_by(Manager.id).order_by(func.sum(Order.total_amount).desc()).all()

        # Prepare data for the bar chart
        total_sales_data = {
            "labels": [row.manager_name for row in sales_by_manager_query],  # Manager names
            "values": [float(row.total_sales) for row in sales_by_manager_query],  # Total sales
        }

        # Chart 2: Sales by Item Name
        sales_by_item_query = db.session.query(
            FoodItem.item_name,
            func.sum(OrderItem.price).label('total_sales')
        ).join(OrderItem, FoodItem.id == OrderItem.item_id)\
        .group_by(FoodItem.item_name).all()

        sales_by_item = {
            "labels": [item[0] for item in sales_by_item_query[:10]],
            "values": [float(item[1]) for item in sales_by_item_query[:10]]
        }

        # Chart 3: Quantity Sold Over Time
        quantity_sold_query = db.session.query(
            func.date(FoodItem.created_at).label('sale_date'),
            func.sum(OrderItem.quantity).label('total_quantity')
        ).group_by(func.date(FoodItem.created_at)).all()

        # Ensure that query results are processed
        quantity_sold_over_time = {
            "labels": [str(row[0]) for row in quantity_sold_query],  # Convert dates to strings
            "values": [int(row[1]) for row in quantity_sold_query]  # Ensure values are integers
        }

        # Chart 4: Top-Selling Items
        top_selling_items_query = db.session.query(
            FoodItem.item_name,
            func.sum(OrderItem.quantity).label('total_quantity')
        ).join(OrderItem, FoodItem.id == OrderItem.item_id)\
        .group_by(FoodItem.item_name)\
        .order_by(func.sum(OrderItem.quantity).desc())\
        .limit(10).all()

        top_item_names = [item[0] for item in top_selling_items_query[:10]]
        top_item_quantities = [int(item[1]) for item in top_selling_items_query[:10]]

        top_selling_items = {
            'labels': top_item_names,
            'values': top_item_quantities,
        }

        # Chart 5: Sales Distribution by Item
        sales_distribution = db.session.query(
            Order.order_status,
            func.count(Order.order_id).label('status_count')
        ).group_by(Order.order_status).all()

        # Prepare data for the pie chart
        distribution_labels = [status[0] for status in sales_distribution]  
        distribution_values = [int(status[1]) for status in sales_distribution]

        # Chart 6: Daily Sales Performance
        daily_sales_performance = db.session.query(
            func.date(FoodItem.created_at).label('sale_date'),
            func.sum(FoodItem.price).label('total_revenue')
        ).group_by(func.date(FoodItem.created_at))\
        .order_by(func.date(FoodItem.created_at)).all()

        performance_dates = [str(row[0]) for row in daily_sales_performance]
        total_revenues = [float(row[1]) for row in daily_sales_performance]

        notification_check = check_notification(role, user_id)

    except Exception as e:
        print(f"Error fetching data: {e}")

    # Render the admin dashboard template
    return render_template(
        'admin/admin_dashboard.html',
        total_sales_amount=total_sales_amount,
        total_orders_count=total_orders_count,
        quantity_sold=quantity_sold,
        sales_data=sales_data,
        user_name=user.name,
        notification_check=len(notification_check),
        role=role,
        months=months,
        total_sales=total_sales,
        total_sales_data=total_sales_data,
        barChartData=barChartData,
        encoded_image=encoded_image,
        kitchen_names=kitchen_names,
        order_counts=order_counts,
        sales_by_item=sales_by_item,
        top_selling_items = top_selling_items,
        quantity_sold_over_time=quantity_sold_over_time,
        #status_distribution=status_distribution,
        #top_selling_items={"labels": top_item_names, "values": top_item_quantities},
        sales_distribution={"labels": distribution_labels, "values": distribution_values},
        daily_sales_performance={"labels": performance_dates, "values": total_revenues}
    )

###################################### Route for displaying manager dashboard #########################
@dashboard_bp.route('/manager', methods=['GET'])
@role_required('Manager')
def manager_dashboard():
    from models import SuperDistributor, Distributor, Kitchen, FoodItem, OrderItem, Order, Sales, Manager

    role = session.get('role')
    user_id = session.get('user_id')
    user = get_user_query(role, user_id)
    encoded_image = get_image(role, user_id)
    notification_check = check_notification(role, user_id)

    total_sales_amount, total_orders_count, quantity_sold, total_sales_data, sales_by_item = 0, 0, 0, 0, 0
    sales_data, monthly_sales = [], []
    months, total_sales, top_selling_items = [], [], 0
    barChartData = {"labels": ["January", "February", "March", "April"], "values": [10, 20, 15, 30]}
    
    # Initialize the variables to avoid UnboundLocalError
    performance_dates, total_revenues = [], []
    distribution_values, distribution_labels, sale_dates, total_sales = [], [], [], []
    total_sales_data = {"labels": [], "values": []}

  # Initialize with an empty dictionary

    try:
        # Get Manager's specific data (based on logged-in Manager's role)
        manager = Manager.query.filter_by(id=user_id).first()

        if not manager:
            raise Exception("Manager not found")

        # Aggregate totals for the logged-in Manager
        total_sales_amount = (
            db.session.query(db.func.sum(Order.total_amount))  
            .join(Kitchen, Order.kitchen_id == Kitchen.id)  
            .join(Distributor, Kitchen.distributor_id == Distributor.id)  
            .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id)  
            .filter(SuperDistributor.manager_id == user_id)  
            .scalar() or 0 
        )
        
        print("Total Sales Amount: ", total_sales_amount)
        total_orders_count = (
            db.session.query(db.func.count(Order.order_id))  
            .join(Kitchen, Order.kitchen_id == Kitchen.id)  
            .join(Distributor, Kitchen.distributor_id == Distributor.id) 
            .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id) 
            .filter(SuperDistributor.manager_id == user_id)  
            .scalar() or 0  
        )

        quantity_sold = (
            db.session.query(db.func.sum(OrderItem.quantity))
            .join(Order, OrderItem.order_id == Order.order_id)  
            .join(Kitchen, Order.kitchen_id == Kitchen.id)  
            .join(Distributor, Kitchen.distributor_id == Distributor.id)  
            .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id)  
            .filter(SuperDistributor.manager_id == user_id)  
            .scalar() or 0  
        )

        # Sales data for the logged-in Manager
        sales_data = (
            db.session.query(
                Sales.sale_id,
                Sales.datetime,
                FoodItem.item_name,
                db.func.sum(OrderItem.price).label("total_price"),
                db.func.sum(OrderItem.quantity).label("total_quantity"),
            )
            .join(Order, Sales.order_id == Order.order_id) 
            .join(OrderItem, Order.order_id == OrderItem.order_id)
            .join(FoodItem, OrderItem.item_id == FoodItem.id)
            .join(Kitchen, Order.kitchen_id == Kitchen.id)
            .join(Distributor, Kitchen.distributor_id == Distributor.id)
            .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id)
            .join(Manager, SuperDistributor.manager_id == Manager.id)
            .filter(Manager.id == user_id)
            .group_by(Sales.sale_id, Sales.datetime, FoodItem.item_name)
            .all()
        )
        
        # Monthly sales for the logged-in Manager
        monthly_sales = db.session.query(
            func.date_format(Sales.datetime, '%Y-%m').label('month'),
            func.sum(Order.total_amount).label('total_sales')
        ).join(Order, Sales.order_id == Order.order_id)\
        .join(Kitchen, Order.kitchen_id == Kitchen.id)\
        .join(Distributor, Kitchen.distributor_id == Distributor.id)\
        .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id)\
        .join(Manager, SuperDistributor.manager_id == Manager.id)\
        .filter(Manager.id == user_id)\
        .group_by(func.date_format(Sales.datetime, '%Y-%m'))\
        .order_by(func.date_format(Sales.datetime, '%Y-%m'))\
        .all()

            # Chart 1: Total Sales by Manager
        sales_by_manager_query = db.session.query(
            Manager.name.label("manager_name"),
            func.sum(Order.total_amount).label("total_sales")
        ).join(SuperDistributor, Manager.id == SuperDistributor.manager_id)\
        .join(Distributor, SuperDistributor.id == Distributor.super_distributor)\
        .join(Kitchen, Distributor.id == Kitchen.distributor_id)\
        .join(Order, Kitchen.id == Order.kitchen_id)\
        .join(Sales, Sales.order_id == Order.order_id)\
        .group_by(Manager.id)\
        .order_by(func.sum(Order.total_amount).desc())\
        .all()

        if sales_by_manager_query:
            total_sales_data = {
                "labels": [row.manager_name for row in sales_by_manager_query],
                "values": [float(row.total_sales) for row in sales_by_manager_query],
            }
        else:
            total_sales_data = {"labels": [], "values": []}

        # Sales By Item
        sales_by_item_query = (
            db.session.query(
                FoodItem.item_name,
                db.func.sum(OrderItem.price).label("total_sales"),
            )
            .join(OrderItem, FoodItem.id == OrderItem.item_id)
            .join(Order, OrderItem.order_id == Order.order_id)
            .join(Kitchen, Order.kitchen_id == Kitchen.id)
            .join(Distributor, Kitchen.distributor_id == Distributor.id)
            .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id)
            .join(Manager, SuperDistributor.manager_id == Manager.id)
            .filter(Manager.id == user_id)  # Filtering by Manager ID
            .group_by(FoodItem.item_name)
            .all()
        )

        sales_by_item = {
            "labels": [item[0] for item in (sales_by_item_query or [])],
            "values": [float(item[1]) for item in (sales_by_item_query or [])],
        }

        # Query for Sales Over Time (grouped by date)
        sales_over_time_query = (
            db.session.query(
                func.date(Sales.datetime).label('sale_date'),  # Group by date
                db.func.sum(OrderItem.price).label("total_sales")  # Sum of total sales
            )
            .join(Order, Sales.order_id == Order.order_id) 
            .join(OrderItem, Order.order_id == OrderItem.order_id)
            .join(FoodItem, OrderItem.item_id == FoodItem.id)
            .join(Kitchen, Order.kitchen_id == Kitchen.id)
            .join(Distributor, Kitchen.distributor_id == Distributor.id)
            .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id)
            .join(Manager, SuperDistributor.manager_id == Manager.id)
            .filter(Manager.id == user_id)
            .group_by(func.date(Sales.datetime))  # Group by date only
            .order_by(func.date(Sales.datetime))  # Order by date
            .all()
        )
        
        # Process the query result
        sale_dates = []
        total_sales = []
        if sales_over_time_query:
            sale_dates = [str(row.sale_date) for row in sales_over_time_query]  # Date as string
            total_sales = [float(row.total_sales) for row in sales_over_time_query]  # Total sales for each date

        # Top-Selling Items
        top_selling_items_query = (
            db.session.query(
                FoodItem.item_name,
                db.func.sum(OrderItem.quantity).label("total_quantity"),
            )
            .join(OrderItem, FoodItem.id == OrderItem.item_id)
            .join(Order, OrderItem.order_id == Order.order_id)
            .join(Kitchen, Order.kitchen_id == Kitchen.id)
            .join(Distributor, Kitchen.distributor_id == Distributor.id)
            .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id)
            .join(Manager, SuperDistributor.manager_id == Manager.id)
            .filter(Manager.id == user_id)  # Filtering by Manager ID
            .group_by(FoodItem.item_name)
            .order_by(db.func.sum(OrderItem.quantity).desc())
            .limit(10)
            .all()
        )

        top_selling_items = {
            "labels": [item[0] for item in (top_selling_items_query or [])],
            "values": [int(item[1]) for item in (top_selling_items_query or [])],
        }
        
        # Query for Daily Sales Performance
        daily_sales_performance_query = db.session.query(
            func.date(FoodItem.created_at).label('sale_date'),
            func.sum(FoodItem.price).label('total_revenue')
        ).join(OrderItem, FoodItem.id == OrderItem.item_id)\
        .join(Order, OrderItem.order_id == Order.order_id)\
        .join(Kitchen, Order.kitchen_id == Kitchen.id)\
        .group_by(func.date(FoodItem.created_at))\
        .order_by(func.date(FoodItem.created_at)).all()

        performance_dates = []
        total_revenues = []
        if daily_sales_performance_query:
            performance_dates = [str(row.sale_date) for row in daily_sales_performance_query]
            total_revenues = [float(row.total_revenue) for row in daily_sales_performance_query]

        # Query for Sales Distribution by Food Item
        sales_distribution_query = db.session.query(
            FoodItem.item_name.label('item_name'),
            func.sum(FoodItem.price).label('total_revenue')
        ).join(OrderItem, FoodItem.id == OrderItem.item_id)\
        .join(Order, OrderItem.order_id == Order.order_id)\
        .join(Kitchen, Order.kitchen_id == Kitchen.id)\
        .group_by(FoodItem.item_name)\
        .order_by(func.sum(FoodItem.price).desc()).all()

        distribution_labels = []
        distribution_values = []
        if sales_distribution_query:
            distribution_labels = [row.item_name for row in sales_distribution_query[:5]]
            distribution_values = [float(row.total_revenue) for row in sales_distribution_query[:5]]

    except Exception as e:
        print(f"Error fetching data: {e}")

    return render_template(
        'manager/manager_dashboard.html',
        notification_check=len(notification_check),
        total_sales_amount=total_sales_amount,
        total_orders_count=total_orders_count,
        quantity_sold=quantity_sold,
        sales_data=sales_data,
        user_name=user.name,
        role=role,
        months=months,
        monthly_sales=monthly_sales,
        total_sales=total_sales,
        total_sales_data=total_sales_data,
        barChartData=barChartData,
        encoded_image=encoded_image,
        sales_by_item=sales_by_item,
        top_selling_items=top_selling_items,
        daily_sales_performance={
            "labels": performance_dates,
            "values": total_revenues
        },
        sales_distribution={
            "labels": distribution_labels,
            "values": distribution_values
        },
            sales_over_time={
        "labels": sale_dates,
        "values": total_sales
        }
    )

###################################### Route for displaying distributor dashboard #####################
@dashboard_bp.route('/super_distributor', methods=['GET'])
@role_required('SuperDistributor')  
def super_distributor_dashboard():
    from models import Distributor, Kitchen
    role = session.get('role')
    user_id = session.get('user_id')
    image_data = get_image(role, user_id) 
    user = get_user_query(role, user_id)
    notification_check = check_notification(role, user_id)

    total_sales_amount = 0
    total_orders_count = 0
    kitchen_names = []
    order_counts = []
    quantity_sold = 0
    total_sales_data = {"labels": [], "values": []}
    sales_data = {"labels": [], "values": []}
    quantity_sold_data = {"labels": [], "values": []}
    top_selling_items = {"labels": [], "values": []}
    sales_distribution_data = {"labels": [], "values": []}
    daily_sales_data = {"labels": [], "values": []}
    try:
        distributors = Distributor.query.filter_by(super_distributor=user_id).all()
        distributor_count = len(distributors)
        distributor_ids = [distributor.id for distributor in distributors]

        kitchens = Kitchen.query.filter(Kitchen.distributor_id.in_(distributor_ids)).all()
        kitchen_count = len(kitchens)
        kitchen_ids = [kitchen.id for kitchen in kitchens]
        kitchen_names = [kitchen.name for kitchen in kitchens]

        orders = Order.query.filter(Order.kitchen_id.in_(kitchen_ids)).all()
        total_orders_count = len(orders)

        total_sales_amount = (db.session.query(func.sum(Order.total_amount))
            .join(Sales, Sales.order_id == Order.order_id)  # Join Sales with Order using order_id
            .filter(Order.kitchen_id.in_(kitchen_ids))     # Filter by kitchen_id from kitchens_ids
            .scalar() or 0                                  # Default to 0 if no result
        )


        sales = Sales.query.filter(Sales.kitchen_id.in_([kitchen.id for kitchen in kitchens])).all()
        # total_orders_count = len(sales)  # Total number of orders (sales records)
        #total_quantity_sold = 0
        quantity_sold = (
            db.session.query(db.func.sum(OrderItem.quantity))
        .join(Order, OrderItem.order_id == Order.order_id)  
        .join(Kitchen, Order.kitchen_id == Kitchen.id)  
        .join(Distributor, Kitchen.distributor_id == Distributor.id)  
        .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id)  
        .filter(SuperDistributor.id == user_id)  # Compare directly with user_id in SuperDistributor
        .scalar() or 0  
        )

        orders = Order.query.filter(Order.kitchen_id.in_(kitchen_ids)).all()
        total_orders_count = len(orders)

        total_sales_amount = db.session.query(func.sum(Order.total_amount)).filter(
            Order.kitchen_id.in_(kitchen_ids)
        ).scalar() or 0

        # 1. Chart for total sales by distributor
        sales_by_distributor_query = db.session.query(
            Distributor.name.label("distributor_name"),
            func.sum(Order.total_amount).label("total_sales")
        ).join(Kitchen, Distributor.id == Kitchen.distributor_id) \
        .join(Order, Kitchen.id == Order.kitchen_id) \
        .join(Sales, Sales.order_id == Order.order_id) \
        .filter(Distributor.super_distributor == user_id) \
        .group_by(Distributor.id) \
        .order_by(func.sum(Order.total_amount).desc()) \
        .all()
        
        total_sales_data = {
                "labels": [row.distributor_name for row in sales_by_distributor_query],
                "values": [float(row.total_sales) for row in sales_by_distributor_query],
            }

        # 2. Chart for Sales by item

        sales_by_item_query = db.session.query(
            FoodItem.item_name,
            func.sum(Order.total_amount).label('total_sales')
        ).join(OrderItem, Order.order_id == OrderItem.order_id) \
        .join(FoodItem, OrderItem.item_id == FoodItem.id) \
        .join(Kitchen, FoodItem.kitchen_id == Kitchen.id) \
        .join(Distributor, Kitchen.distributor_id == Distributor.id) \
        .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id) \
        .filter(SuperDistributor.id == user_id) \
        .group_by(FoodItem.item_name) \
        .all()

        # Convert results into a list of dictionaries
        sales_data = {
            "labels": [row.item_name if row.item_name else '' for row in sales_by_item_query],  # Ensure item_name is not None
            "values": [float(row.total_sales) if row.total_sales is not None else 0.0 for row in sales_by_item_query],  # Ensure total_sales is not None
        }

        # Chart 3: Quantity Sold Over Time

        quantity_sold_query = db.session.query(
            func.date(FoodItem.created_at).label('sale_date'),
            func.sum(OrderItem.quantity).label('total_quantity')
        ).join(OrderItem, FoodItem.id == OrderItem.item_id) \
        .join(Order, Order.order_id == OrderItem.order_id) \
        .join(Kitchen, FoodItem.kitchen_id == Kitchen.id) \
        .join(Distributor, Kitchen.distributor_id == Distributor.id) \
        .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id) \
        .filter(SuperDistributor.id == user_id) \
        .group_by(func.date(FoodItem.created_at)) \
        .all()

        # Convert results into a list of dictionaries
        quantity_sold_data = {
            "labels": [row.sale_date.strftime('%Y-%m-%d') if row.sale_date else '' for row in quantity_sold_query],  # Ensure sale_date is not None
            "values": [int(row.total_quantity) if row.total_quantity is not None else 0 for row in quantity_sold_query],  # Ensure total_quantity is not None
        }

        # Chart 3: Top Selling Item

        top_selling_items_query = db.session.query(
            FoodItem.item_name,
            func.sum(OrderItem.quantity).label('total_quantity')
        ).join(OrderItem, FoodItem.id == OrderItem.item_id) \
        .join(Order, Order.order_id == OrderItem.order_id) \
        .join(Kitchen, FoodItem.kitchen_id == Kitchen.id) \
        .join(Distributor, Kitchen.distributor_id == Distributor.id) \
        .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id) \
        .filter(SuperDistributor.id == user_id) \
        .group_by(FoodItem.item_name) \
        .order_by(func.sum(OrderItem.quantity).desc()) \
        .limit(10).all()

        # Extract item names and quantities
        top_item_names = [item[0] if item[0] else '' for item in top_selling_items_query]  # Ensure item_name is not None
        top_item_quantities = [int(item[1]) if item[1] is not None else 0 for item in top_selling_items_query]  # Ensure total_quantity is not None

        # Prepare the dictionary
        top_selling_items = {
            'labels': top_item_names,
            'values': top_item_quantities,
        }

        # Chart 5: Sales Distribution by Item
        sales_distribution = db.session.query(
            FoodItem.item_name,
            func.sum(OrderItem.price).label('total_sales')
        ).join(OrderItem, FoodItem.id == OrderItem.item_id) \
        .join(Order, Order.order_id == OrderItem.order_id) \
        .join(Kitchen, FoodItem.kitchen_id == Kitchen.id) \
        .join(Distributor, Kitchen.distributor_id == Distributor.id) \
        .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id) \
        .filter(SuperDistributor.id == user_id) \
        .group_by(FoodItem.item_name).all()

        # Extract item names and sales values
        distribution_labels = [item[0] if item[0] else '' for item in sales_distribution]  # Ensure item_name is not None
        distribution_values = [float(item[1]) if item[1] is not None else 0.0 for item in sales_distribution]  # Ensure total_sales is not None

        # Prepare the result dictionary
        sales_distribution_data = {
            'labels': distribution_labels,
            'values': distribution_values,
        }

        # Chart 6: Daily Sales Performance
        daily_sales_performance = db.session.query(
            func.date(Order.created_at).label('sale_date'),
            func.sum(OrderItem.price).label('total_revenue')
        ).join(OrderItem, Order.order_id == OrderItem.order_id) \
        .join(FoodItem, OrderItem.item_id == FoodItem.id) \
        .join(Kitchen, FoodItem.kitchen_id == Kitchen.id) \
        .join(Distributor, Kitchen.distributor_id == Distributor.id) \
        .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id) \
        .filter(SuperDistributor.id == user_id) \
        .group_by(func.date(Order.created_at)) \
        .order_by(func.date(Order.created_at)).all()

        # Extract performance dates and revenues
        performance_dates = [row.sale_date.strftime('%Y-%m-%d') if row.sale_date else '' for row in daily_sales_performance]  # Ensure sale_date is not None
        total_revenues = [float(row.total_revenue) if row.total_revenue is not None else 0.0 for row in daily_sales_performance]  # Ensure total_revenue is not None

        # Prepare the result dictionary
        daily_sales_data = {
            'labels': performance_dates,
            'values': total_revenues,
        }
    except Exception as e:
        print(f"Error fetching data: {e}")

    return render_template('super_distributor/sd_dashboard.html',
                           user_id=user_id,
                           user_name=user.name,
                           role=role,
                           total_sales_data=total_sales_data,
                           encoded_image=image_data,
                           total_sales_amount=total_sales_amount,
                           total_orders_count=total_orders_count,
                           kitchen_names=kitchen_names,
                           sales_data=sales_data,
                           quantity_sold_data=quantity_sold_data,
                           top_selling_items=top_selling_items,
                           sales_distribution_data=sales_distribution_data,
                           daily_sales_data=daily_sales_data,
                           order_counts=order_counts,
                           quantity_sold=quantity_sold,
                           notification_check=len(notification_check))


###################################### Route for displaying distributor dashboard #####################
@dashboard_bp.route('/distributor', methods=['GET'])
@role_required('Distributor')  
def distributor_dashboard():
    from models import Kitchen
    role = session.get('role')
    user_id = session.get('user_id')
    image_data = get_image(role, user_id) 
    user = get_user_query(role, user_id)
    notification_check = check_notification(role, user_id)
    
    try:
        # Query to get kitchen ids
        kitchens = Kitchen.query.filter_by(distributor_id=user_id).all()
        kitchen_count = len(kitchens)
        kitchens_ids = [kitchen.id for kitchen in kitchens]

        #Query for total sales amount
        total_sales_amount = (
            db.session.query(func.sum(Order.total_amount))
            .join(Sales, Sales.order_id == Order.order_id)  # Join Sales with Order using order_id
            .filter(Order.kitchen_id.in_(kitchens_ids))     # Filter by kitchen_id from kitchens_ids
            .scalar() or 0                                  # Default to 0 if no result
        )

        #Query for total order count
        orders = Order.query.filter(Order.kitchen_id.in_(kitchens_ids)).all()
        total_orders_count = len(orders)

        #Query for quantity sold count
        quantity_sold = (
            db.session.query(db.func.sum(OrderItem.quantity))
        .join(Order, OrderItem.order_id == Order.order_id)  
        .join(Kitchen, Order.kitchen_id == Kitchen.id)
        .join(Sales, Sales.order_id == Order.order_id) 
        .join(Distributor, Kitchen.distributor_id == Distributor.id) 
        .filter(Distributor.id == user_id) 
        .scalar() or 0  
        )

        # chrt 1. For sales by kitchen
        sales_by_kitchen_query = db.session.query(
            Kitchen.name.label("kitchen_name"),
            func.sum(Order.total_amount).label("total_sales")
        ).join(Order, Kitchen.id == Order.kitchen_id) \
        .join(Sales, Sales.order_id == Order.order_id) \
        .filter(Kitchen.distributor_id == user_id) \
        .group_by(Kitchen.id) \
        .order_by(func.sum(Order.total_amount).desc()) \
        .all()
        total_sales_data = {
                "labels": [row.kitchen_name for row in sales_by_kitchen_query],
                "values": [float(row.total_sales) for row in sales_by_kitchen_query],
            }
        
        # 2. Chart for Sales by item

        sales_by_item_query = db.session.query(
            FoodItem.item_name,
            func.sum(Order.total_amount).label('total_sales')
        ).join(OrderItem, Order.order_id == OrderItem.order_id) \
        .join(FoodItem, OrderItem.item_id == FoodItem.id) \
        .join(Kitchen, FoodItem.kitchen_id == Kitchen.id) \
        .join(Distributor, Kitchen.distributor_id == Distributor.id) \
        .filter(Distributor.id == user_id) \
        .group_by(FoodItem.item_name) \
        .all()

        # Convert results into a list of dictionaries
        sales_data = {
            "labels": [row.item_name if row.item_name else '' for row in sales_by_item_query],  # Ensure item_name is not None
            "values": [float(row.total_sales) if row.total_sales is not None else 0.0 for row in sales_by_item_query],  # Ensure total_sales is not None
        }

        # Chart 4: Quantity Sold Over Time

        quantity_sold_query = db.session.query(
            func.date(FoodItem.created_at).label('sale_date'),
            func.sum(OrderItem.quantity).label('total_quantity')
        ).join(OrderItem, FoodItem.id == OrderItem.item_id) \
        .join(Order, Order.order_id == OrderItem.order_id) \
        .join(Sales, Sales.order_id == Order.order_id).join(Kitchen, FoodItem.kitchen_id == Kitchen.id) \
        .join(Distributor, Kitchen.distributor_id == Distributor.id) \
        .filter(Distributor.id == user_id) \
        .group_by(func.date(FoodItem.created_at)) \
        .all()

        # Convert results into a list of dictionaries
        quantity_sold_data = {
            "labels": [row.sale_date.strftime('%Y-%m-%d') if row.sale_date else '' for row in quantity_sold_query],  # Ensure sale_date is not None
            "values": [int(row.total_quantity) if row.total_quantity is not None else 0 for row in quantity_sold_query],  # Ensure total_quantity is not None
        }

        # Chart 3: Top Selling Item

        top_selling_items_query = db.session.query(
            FoodItem.item_name,
            func.sum(OrderItem.quantity).label('total_quantity')
        ).join(OrderItem, FoodItem.id == OrderItem.item_id) \
        .join(Order, Order.order_id == OrderItem.order_id) \
        .join(Kitchen, FoodItem.kitchen_id == Kitchen.id) \
        .join(Distributor, Kitchen.distributor_id == Distributor.id) \
        .filter(Distributor.id == user_id) \
        .group_by(FoodItem.item_name) \
        .order_by(func.sum(OrderItem.quantity).desc()) \
        .limit(10).all()

        # Extract item names and quantities
        top_item_names = [item[0] if item[0] else '' for item in top_selling_items_query]  # Ensure item_name is not None
        top_item_quantities = [int(item[1]) if item[1] is not None else 0 for item in top_selling_items_query]  # Ensure total_quantity is not None

        # Prepare the dictionary
        top_selling_items = {
            'labels': top_item_names,
            'values': top_item_quantities,
        }

        # Chart 5: Sales Distribution by Item
        sales_distribution = db.session.query(
            FoodItem.item_name,
            func.sum(OrderItem.price).label('total_sales')
        ).join(OrderItem, FoodItem.id == OrderItem.item_id) \
        .join(Order, Order.order_id == OrderItem.order_id) \
        .join(Kitchen, FoodItem.kitchen_id == Kitchen.id) \
        .join(Distributor, Kitchen.distributor_id == Distributor.id) \
        .filter(Distributor.id == user_id) \
        .group_by(FoodItem.item_name).all()

        # Extract item names and sales values
        distribution_labels = [item[0] if item[0] else '' for item in sales_distribution]  # Ensure item_name is not None
        distribution_values = [float(item[1]) if item[1] is not None else 0.0 for item in sales_distribution]  # Ensure total_sales is not None

        # Prepare the result dictionary
        sales_distribution_data = {
            'labels': distribution_labels,
            'values': distribution_values,
        }

        # Chart 6: Daily Sales Performance
        daily_sales_performance = db.session.query(
            func.date(Order.created_at).label('sale_date'),
            func.sum(OrderItem.price).label('total_revenue')
        ).join(OrderItem, Order.order_id == OrderItem.order_id) \
        .join(FoodItem, OrderItem.item_id == FoodItem.id) \
        .join(Kitchen, FoodItem.kitchen_id == Kitchen.id) \
        .join(Distributor, Kitchen.distributor_id == Distributor.id) \
        .filter(Distributor.id == user_id) \
        .group_by(func.date(Order.created_at)) \
        .order_by(func.date(Order.created_at)).all()

        # Extract performance dates and revenues
        performance_dates = [row.sale_date.strftime('%Y-%m-%d') if row.sale_date else '' for row in daily_sales_performance]  # Ensure sale_date is not None
        total_revenues = [float(row.total_revenue) if row.total_revenue is not None else 0.0 for row in daily_sales_performance]  # Ensure total_revenue is not None

        # Prepare the result dictionary
        daily_sales_data = {
            'labels': performance_dates,
            'values': total_revenues,
        }

    except Exception as e:
        print(f"Error fetching data: {e}")

    return render_template('distributor/d_dashboard.html',
                           user_id=user_id,
                           user_name=user.name,
                           role=role,
                           encoded_image=image_data,
                           total_sales_amount = total_sales_amount,
                           total_orders_count=total_orders_count,
                           quantity_sold=quantity_sold,
                           total_sales_data=total_sales_data,
                           sales_data=sales_data,
                           quantity_sold_data=quantity_sold_data,
                           top_selling_items=top_selling_items,
                           sales_distribution_data=sales_distribution_data,
                           daily_sales_data=daily_sales_data,
                           notification_check=len(notification_check)
                           )

###################################### Route for displaying kitchen dashboard #########################
from collections import Counter
@dashboard_bp.route('/kitchen', methods=['GET'])
@role_required('Kitchen')  
def kitchen_dashboard():
    from models import Kitchen
    role = session.get('role')
    user_id = session.get('user_id')
    image_data = get_image(role, user_id) 
    user = get_user_query(role, user_id)
    notification_check = check_notification(role, user_id)

    try:
        total_sales_amount = (
        db.session.query(func.sum(Order.total_amount))
        .join(Sales, Order.order_id == Sales.order_id)  # Join Order with Sales
        .filter(Order.kitchen_id == user_id)           # Filter by kitchen_id
        .scalar() or 0                                 # Default to 0 if no result
        ) 

        quantity_sold = (
            db.session.query(db.func.sum(OrderItem.quantity))
            .join(Order, OrderItem.order_id == Order.order_id)  # Join OrderItem with Order
            .join(Sales, Sales.order_id == Order.order_id)      # Join Order with Sales
            .join(Kitchen, Order.kitchen_id == Kitchen.id)      # Join Order with Kitchen
            .filter(Kitchen.id == user_id)                       # Filter by kitchen_id
            .scalar() or 0                                       # Default to 0 if no result
        )
        # Query all orders for the specific kitchen
        orders = Order.query.filter(Order.kitchen_id == user_id).all()
        order_dates = [order.created_at.date() for order in orders]
        order_counts = Counter(order_dates)
        order_data = {
            'labels': [date.strftime('%Y-%m-%d') for date, _ in sorted(order_counts.items())],
            'values': [count for _, count in sorted(order_counts.items())]
        }
        # Count total orders
        total_orders_count = len(orders)

        # Query grouped by status
        status_counts = (
            Order.query.with_entities(Order.order_status, func.count(Order.order_id).label("count"))
            .filter(Order.kitchen_id == user_id)
            .group_by(Order.order_status)
            .all()
        )

        # Convert the result into a dictionary
        status_counts_dict = {status: count for status, count in status_counts}

        # Add missing statuses with a count of 0
        all_statuses = ["Completed", "Cancelled", "Pending", "Processing"]
        for status in all_statuses:
            if status not in status_counts_dict:
                status_counts_dict[status] = 0


        # Define a variable to determine the type of filter ('daily', 'weekly', or 'monthly')
        filter_type = request.args.get('filter_type', 'daily')  # This can be dynamically set based on user input

        # Build the query dynamically based on the filter type
        if filter_type == 'daily':
            group_by = func.date(Order.created_at)  # Group by date
            label = 'sale_date'
        elif filter_type == 'weekly':
            group_by = func.week(Order.created_at)  # Group by week
            label = 'week'
        elif filter_type == 'monthly':
            group_by = func.date_format(Order.created_at, '%Y-%m')  # Group by Year-Month
            label = 'month'
        else:
            raise ValueError("Invalid filter type")

        # Query to get daily, weekly, or monthly sales data
        daily_sales_performance = db.session.query(
            group_by.label(label),  # Grouping by the respective time period
            func.sum(OrderItem.price).label('total_revenue')
        ).join(OrderItem, Order.order_id == OrderItem.order_id) \
        .join(FoodItem, OrderItem.item_id == FoodItem.id) \
        .join(Kitchen, FoodItem.kitchen_id == Kitchen.id) \
        .filter(Kitchen.id == user_id) \
        .group_by(group_by) \
        .order_by(group_by).all()

        # Extract performance dates and revenues
        performance_dates = []
        for row in daily_sales_performance:
            # For daily grouping: check if row[0] is a datetime or a string
            if isinstance(row[0], datetime):  # Check if the value is a datetime object (for daily grouping)
                performance_dates.append(row[0].strftime('%Y-%m-%d'))  # Format as date (e.g., '2024-12-19')
            elif isinstance(row[0], str):  # If it's already a string (which might happen for some DB types)
                performance_dates.append(row[0])  # Just use the string format (e.g., '2024-12-19')
            elif isinstance(row[0], int):  # For weekly grouping (int)
                performance_dates.append(f"Week {row[0]}")  # Format as 'Week {week_number}'
            else:
                performance_dates.append(str(row[0]))  # Default fallback

        # Total revenues
        total_revenues = [float(row.total_revenue) if row.total_revenue is not None else 0.0 for row in daily_sales_performance]

        # Prepare the result dictionary
        sales_data = {
            'labels': performance_dates,
            'values': total_revenues,
        }

        # Chart 3: Top Selling Item

        top_selling_items_query = db.session.query(
            FoodItem.item_name,
            func.sum(OrderItem.quantity).label('total_quantity')
        ).join(OrderItem, FoodItem.id == OrderItem.item_id) \
        .join(Order, Order.order_id == OrderItem.order_id) \
        .join(Kitchen, FoodItem.kitchen_id == Kitchen.id) \
        .filter(Kitchen.id == user_id) \
        .group_by(FoodItem.item_name) \
        .order_by(func.sum(OrderItem.quantity).desc()) \
        .limit(10).all()

        # Extract item names and quantities
        top_item_names = [item[0] if item[0] else '' for item in top_selling_items_query[:5]]  # Ensure item_name is not None
        top_item_quantities = [int(item[1]) if item[1] is not None else 0 for item in top_selling_items_query[:5]]  # Ensure total_quantity is not None

        # Prepare the dictionary
        top_selling_items = {
            'labels': top_item_names,
            'values': top_item_quantities,
        }
        

    except Exception as e:
        print(f"Error fetching data: {e}")
        
    return render_template('kitchen/kitchen_dashboard.html',
                           user_id=user_id,
                           user_name=user.name,
                           role=role,
                           encoded_image=image_data,
                           total_sales_amount=total_sales_amount,
                           total_orders_count=total_orders_count,
                           status_counts=status_counts_dict,
                           quantity_sold=quantity_sold,
                           filter_type=filter_type,
                           daily_sales_data=sales_data,
                           top_selling_items=top_selling_items,
                           order_data =order_data,
                           notification_check=len(notification_check)
                    )

def cpunt_func(self, user_id):
    role = session.get('role')
    user_id = session.get('user_id')
    user = get_user_query(role, user_id)
    admin_total_sales_amount = 0
    manager_total_sales_amount = 0
    try:
        admin_total_sales_amount = db.session.query(func.sum(Order.total_amount)).scalar() or 0
        print("admin_total_sales_amount: ", admin_total_sales_amount)
        
        manager_total_sales_amount = (
            db.session.query(db.func.sum(Order.total_amount))  
            .join(Kitchen, Order.kitchen_id == Kitchen.id)  
            .join(Distributor, Kitchen.distributor_id == Distributor.id)  
            .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id)  
            .filter(SuperDistributor.manager_id == user_id)  
            .scalar() or 0 
        )
        print("manager_total_sales_amount: ", manager_total_sales_amount)
    except Exception as e:
        print(f"Error fetching data: {e}")