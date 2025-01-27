###################################### Importing Required Libraries ###################################
from models import db, Sales, Order, OrderItem, FoodItem, Manager, Distributor, SuperDistributor, Kitchen, Admin
from sqlalchemy import func, and_
from base64 import b64encode
from datetime import datetime, time
from collections import defaultdict
from sqlalchemy import func, desc
from flask import session

###################################### Get Model Counts ###############################################
def get_model_counts():
    """Returns a dictionary with counts of all models."""
    return {
        'manager_count': Manager.query.filter_by(status='activated').count(),
        'super_distributor_count': SuperDistributor.query.filter_by(status='activated').count(),
        'distributor_count': Distributor.query.filter_by(status='activated').count(),
        'kitchen_count': Kitchen.query.filter_by(status='activated').count(),
    }

###################################### Allowed File Function ##########################################
def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

################################## globally defined role_model_map ####################################
ROLE_MODEL_MAP = {
    "Admin": Admin,
    "Manager": Manager,
    "SuperDistributor": SuperDistributor,
    "Distributor": Distributor,
    "Kitchen": Kitchen,
}

###################################### Get Model By Role ##############################################
def get_model_by_role(role):
    return ROLE_MODEL_MAP.get(role)

###################################### Get Image Function #############################################
def get_image(role,user_id):

    user_model = ROLE_MODEL_MAP.get(role)
    if not user_model:
        return {'error': 'Invalid role provided'}

    user_instance = user_model.query.get(user_id)
    if not user_instance:
        return {'error': 'User not found'}

    # Encode the image if it exists
    encoded_image = None
    if user_instance.image:
        encoded_image = b64encode(user_instance.image).decode('utf-8')
        
    return encoded_image

###################################### Check Notification Function ####################################
def get_user_query(role, user_id):
       
    model = ROLE_MODEL_MAP.get(role)
    
    if not model:
        raise ValueError(f"Invalid role: {role}. Please check the role and try again.")

    user = model.query.filter_by(id=user_id).first()

    return user

###################################### Today Sale Function ############################################
def today_sale(user_id):
    
    today_start = datetime.combine(datetime.today(), time.min)  # Midnight
    today_end = datetime.combine(datetime.today(), time.max)   # 11:59 PM

    # Query to calculate total sales
    today_total_sales = db.session.query(
            func.sum(Order.total_amount)
        ).join(Sales, Sales.order_id == Order.order_id) \
         .filter(
            and_(
                Sales.kitchen_id == user_id,
                Sales.datetime >= today_start,
                Sales.datetime <= today_end
            )
         ).scalar()
    
    return today_total_sales

###################################### Class For Manager Sales ########################################
class SalesReport():
    def cpunt_func(self, user_id):
        total_sales_amount = (
            db.session.query(db.func.sum(Order.total_amount))  
            .join(Kitchen, Order.kitchen_id == Kitchen.id)  
            .join(Distributor, Kitchen.distributor_id == Distributor.id)  
            .join(SuperDistributor, Distributor.super_distributor == SuperDistributor.id)  
            .filter(SuperDistributor.manager_id == user_id)  
            .scalar() or 0 
        )

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
        return total_sales_amount, total_orders_count, quantity_sold, sales_data
MS = SalesReport()
