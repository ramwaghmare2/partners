###################################### Importing Required Libraries ###################################
from flask import Blueprint, request, jsonify, session, redirect, render_template, flash, current_app, url_for
from utils.notification_service import check_notification, create_notification
from werkzeug.security import check_password_hash, generate_password_hash
from utils.services import get_model_counts , get_image, get_user_query
from models import db, Kitchen, Distributor, FoodItem, Order, Sales
from datetime import datetime, timedelta
from utils.services import allowed_file
from sqlalchemy import func
import bcrypt
import json

###################################### Blueprint For Kitchen ##########################################
kitchen_bp = Blueprint('kitchen', __name__, static_folder='../static')

################################## Route to add a new Kitchen #########################################
@kitchen_bp.route('/kitchens', methods=['GET', 'POST'])
def create_kitchen():
    user_id = session.get('user_id')
    role = session.get('role')
    image_data = get_image(role, user_id)
    user_name = session.get('user_name')
    distributors = Distributor.query.filter_by(status='activated').all()
    data = request.form

    notification_check = check_notification(role, user_id)

    user = get_user_query(role, user_id)
    if request.method == 'POST':
        if role == 'Distributor':
            distributor_id = session.get('user_id')
        else:
            distributor_id = request.form.get('distributor')

        existing_kitchen = Kitchen.query.filter_by(email=data.get('email')).first()
        if existing_kitchen:
            flash("A kitchen with this email already exists. Please use a different email.", 'danger')
            return render_template(
                'kitchen/add_kitchen.html',
                role=role,
                distributors=distributors,
                user_name=user_name,
                encoded_image=image_data
            )

        hashed_password = generate_password_hash(data.get('password'))
        
        # Initialize image_binary to None, to handle cases where no image is uploaded
        image_binary = None

        # Handle image upload if a new image is provided
        image = request.files.get('image')
        if image and allowed_file(image.filename):
            # Convert the image to binary data
            image_binary = image.read()

        new_kitchen = Kitchen(
            name=data.get('name'),
            email=data.get('email'),
            password=hashed_password,  # Ensure to hash passwords in production
            contact=data.get('contact'),
            city=data.get('city'),
            image=image_binary,
            pin_code=data.get('pin_code'),
            state=data.get('state'),
            district=data.get('district'),
            address=data.get('address'),
            distributor_id=distributor_id
        )

        db.session.add(new_kitchen)
        db.session.commit()

        create_notification(user_id=new_kitchen.id,
                            role='Kitchen',
                            notification_type='Add',
                            description=f'{user.name}, the {role}, has Successfully Added {new_kitchen.name}, the Kitchen.')

        flash('Kitchen Added Successfully.', 'success')
        return redirect(url_for('kitchen.create_kitchen'))

    return render_template(
        'kitchen/add_kitchen.html',
        role=role,
        distributors=distributors,
        user_name=user.name,
        encoded_image=image_data,
        notification_check=len(notification_check)
    )


###################################### Route to Get a list of all Kitchens ############################
@kitchen_bp.route('/all-kitchens', methods=['GET'])
def get_kitchens():
    role = session.get('role')
    user_name = session.get('user_name')
    kitchens = Kitchen.query.all()
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 
    counts = get_model_counts()
    return render_template('distributor/d_all_kitchens.html',
                           all_kitchens=kitchens,
                           role=role,
                           user_name=user_name,
                           **counts,
                           encoded_image=image_data)

###################################### Route for edit the super_distributor ###########################
@kitchen_bp.route('/edit/<int:kitchen_id>', methods=['GET', 'POST'])
def edit_kitchen(kitchen_id):
    kitchen = Kitchen.query.get_or_404(kitchen_id)

    role = session.get('role')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 
    user = get_user_query(role, user_id)

    notification_check = check_notification(role, user_id)

    if request.method == 'POST':
        image = request.files.get('image')
        name = request.form['name']
        email = request.form['email']
        contact = request.form.get('contact')
        password = request.form['password']

        # Validate if email already exists (excluding the current kitchen)
        existing_kitchen_email = Kitchen.query.filter(Kitchen.email == email, Kitchen.id != kitchen.id).first()
        if existing_kitchen_email:
            flash("The email is already in use by another Kitchen.", "danger")
            return redirect(url_for('kitchen.edit_kitchen',kitchen_id=kitchen_id))

        # Validate if contact already exists (excluding the current kitchen)
        existing_kitchen_contact = Kitchen.query.filter(Kitchen.contact == contact, Kitchen.id != kitchen.id).first()
        if existing_kitchen_contact:
            flash("The contact number is already in use by another Kitchen.", "danger")
            return redirect(url_for('kitchen.edit_kitchen',kitchen_id=kitchen_id))

        # Update kitchen details
        kitchen.name = name
        kitchen.email = email
        kitchen.contact = contact

        # If password is provided, hash and update it
        if password:
            kitchen.password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Handle image update if a new image is uploaded
        if image and allowed_file(image.filename):
            # Convert the image to binary data
            image_binary = image.read()
            kitchen.image = image_binary

        try:
            db.session.commit()

            create_notification(user_id=kitchen.id, 
                                role='Kitchen', 
                                notification_type='Edit', 
                                description=f'{user.name}, the {role}, has Successfully Edited {kitchen.name}, the Kitchen.')

            flash("Kitchen updated successfully!", "success")
            return redirect(url_for('distributor.distrubutor_all_kitchens'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating Kitchen: {str(e)}", "danger")
            return render_template('kitchen/edit_kitchen.html', kitchen=kitchen, role=role,user_name=user.name, encoded_image =image_data)

    return render_template('kitchen/edit_kitchen.html',
                           kitchen=kitchen,
                           role=role,
                           user_name=user.name,
                           encoded_image=image_data,
                           notification_check=len(notification_check))

###################################### Route for delete the kitchen ###################################
@kitchen_bp.route('/delete/<int:kitchen_id>', methods=['GET', 'POST'])
def delete_kitchen(kitchen_id):
    user_id = session.get('user_id')
    role = session.get('role')
    user = get_user_query(role, user_id)
    kitchen = Kitchen.query.get_or_404(kitchen_id)
    food_items = FoodItem.query.filter_by(kitchen_id=kitchen_id)
    try:
        for item in food_items:
            item.status = 'deactivated'
        kitchen.status = 'deactivated'
        db.session.commit()

        create_notification(user_id=kitchen.id, 
                            role='Kitchen', 
                            notification_type='Delete', 
                            description=f'{user.name}, the {role}, has Successfully Deleted {kitchen.name}, the Kitchen.')

        flash("Kitchen deleted successfully!", "success")
        return redirect(url_for('distributor.distrubutor_all_kitchens'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting manager: {str(e)}", "danger")

    return redirect(url_for('distributor.distrubutor_all_kitchens'))


###################################### Route for Lock/Unlock the kitchen ##############################
@kitchen_bp.route('/lock/<int:kitchen_id>', methods=['GET'])
def lock_kitchen(kitchen_id):
    user_id = session.get('user_id')
    role = session.get('role')
    user = get_user_query(role, user_id)
    kitchen = Kitchen.query.get_or_404(kitchen_id)

    try:
        if kitchen.status == 'activated':
            kitchen.status = 'deactivated'
            db.session.commit()

            create_notification(user_id=kitchen.id, 
                                role='Kitchen', 
                                notification_type='Lock', 
                                description=f'{user.name}, the {role}, has Locked {kitchen.name}, the Kitchen.')

            flash("Kitchen Locked successfully!", "danger")
        else:
            kitchen.status = 'activated'
            db.session.commit()

            create_notification(user_id=kitchen.id, 
                                role='Kitchen', 
                                notification_type='Unlock', 
                                description=f'{user.name}, the {role}, has Unlocked {kitchen.name}, the Kitchen.')

            flash("Kitchen Unlocked successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error : {str(e)}", "danger")

    return redirect(url_for('distributor.distrubutor_all_kitchens'))


###################################### Route for Display Kitchen Dashboard ############################
@kitchen_bp.route("/kitchen_home", methods=['GET', 'POST'])
def kitchen_home():
    user_name = session.get('user_name', 'User')
    role = session.get('role')
    user_id = session.get('user_id')
    image_data = get_image(role, user_id)
    notification_check = check_notification(role, user_id)

    # Filter orders by kitchen_id
    orders = Order.query.filter(Order.kitchen_id == user_id).all()

    # Filter sales by kitchen_id
    sales = Sales.query.filter(Sales.kitchen_id == user_id).all()

    # Count of orders related to the kitchens
    order_count = len(orders)

    # Total price of all orders related to the kitchens
    total_price = db.session.query(func.sum(Order.total_amount)).filter(Order.kitchen_id == user_id).scalar()
    total_price = float(total_price) if total_price else 0  # Convert to float

    kitchen_sales = 0
    for order in orders:
        kitchen_sales += float(order.total_amount)  # Sum the total sales

    # Aggregate order counts and sales by date (daily)
    order_dates = []
    sales_per_date = []
    order_count_per_date = []

    # Aggregating data by day
    for days_offset in range(30):  # For the last 30 days
        date = datetime.now() - timedelta(days=days_offset)
        formatted_date = date.strftime('%Y-%m-%d')
        order_dates.append(formatted_date)
        
        # Count orders and sales for the specific date
        orders_on_date = Order.query.filter(Order.kitchen_id == user_id, func.date(Order.created_at) == date.date()).all()
        order_count_per_date.append(len(orders_on_date))

        sales_on_date = db.session.query(func.sum(Order.total_amount)).filter(Order.kitchen_id == user_id, func.date(Order.created_at) == date.date()).scalar()
        sales_per_date.append(float(sales_on_date) if sales_on_date else 0)

    # Initialize variables to hold the total values
    total_sales_amount = 0
    total_quantity_sold = 0
    total_orders_count = len(sales)  # Total number of orders (sales records)

    # Loop through each sale to calculate total sales amount and quantity sold
    for sale in sales:
        total_sales_amount += sale.orders.total_amount  # Assuming `total_amount` is the sale's total amount
        for item in sale.orders.order_items:  # Assuming there's an order_items relationship
            total_quantity_sold += item.quantity

    return render_template('kitchen/kitchen_index.html',
                           user_name=user_name,
                           user_id=user_id,
                           role=role,
                           encoded_image=image_data,
                           order_count=order_count,
                           total_price=total_price,
                           sales=sales,
                           order_dates=order_dates,
                           sales_per_date=sales_per_date,
                           order_count_per_date=order_count_per_date,
                           total_sales_amount=total_sales_amount,
                           total_quantity_sold=total_quantity_sold,
                           total_orders_count=total_orders_count,
                           notification_check=len(notification_check)
                           )
