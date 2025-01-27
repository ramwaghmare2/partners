###################################### Importing Required Libraries ###################################
from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from models import SuperDistributor, Distributor, Kitchen, Order, Sales, OrderItem, FoodItem
from utils.services import get_model_counts ,allowed_file ,get_image, get_user_query
from utils.notification_service import create_notification, check_notification
from utils.notification_service import check_notification
from werkzeug.security import generate_password_hash
from models.manager import db, Manager
from extensions import bcrypt
from base64 import b64encode
import logging

###################################### Blueprint For Manager ##########################################
manager_bp = Blueprint('manager', __name__,template_folder='../templates/manager', static_folder='../static')

###################################### Route for Add Manager ##########################################
@manager_bp.route('/add', methods=['GET', 'POST'])
def add_manager():

    role = session.get('role')                 # Get the role from  the session
    user_name = session.get('user_name') 
    user_id = session.get('user_id')
    image_data= get_image(role, user_id)       
    user = get_user_query(role, user_id)

    notification_check = check_notification(role, user_id)

    if request.method == 'POST':
        name = request.form['name']     # Get the name from  the form
        email = request.form['email']   # Get the email from  the form
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')  # Hash password
        contact = request.form.get('contact')   # Get the contact from the form
        image = request.files.get('image')  # Get the image from the form

        image_binary = None
        if image and allowed_file(image.filename):
            image_binary = image.read()

        # Check if the email is already in use
        existing_email = Manager.query.filter_by(email=email).first()
        if existing_email:
            flash("Error: Email is already in use.", "danger")
            return render_template('add_manager.html',role=role, user_name=user_name)

        # Check if the contact number is already in use
        existing_contact = Manager.query.filter_by(contact=contact).first()
        if existing_contact:
            flash("Error: Contact number is already in use.", "danger")
            return render_template('add_manager.html',role=role, user_name=user_name)

        # Create manager instance and add to database
        new_manager = Manager(name=name, 
                        email=email, 
                        password=password, 
                        contact=contact,
                        image=image_binary)
        try:
            db.session.add(new_manager)
            db.session.commit()

            create_notification(user_id=new_manager.id, 
                                role='Manager', 
                                notification_type='Add', 
                                description=f'{user.name}, the Admin, has successfully added new Manager, {name}.')


            flash("Manager added successfully!", "success")
            return redirect(url_for('manager.add_manager'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding manager: {str(e)}", "danger")
    
    return render_template('add_manager.html',
                           role=role,
                           user_name=user_name,
                           encoded_image=image_data,
                           notification_check=len(notification_check))

###################################### Route for Get Managers #########################################
@manager_bp.route('/managers', methods=['GET', 'POST'])
def get_managers():
    role = session.get('role')
    user_id = session.get('user_id')
    image_data = get_image(role, user_id)  # Fetch user image
    counts = get_model_counts()  # Fetch model counts (e.g., for dashboard stats)
    user = get_user_query(role, user_id)
    # Get filter status from request parameters
    filter_status = request.args.get('status', 'all').lower()

    try:
        # Decode role and user_name if they are bytes
        role = role.decode('utf-8') if isinstance(role, bytes) else role
        # user_name = user_name.decode('utf-8') if isinstance(user_name, bytes) else user_name

        # Fetch managers based on filter
        if filter_status == 'activated':
            managers = Manager.query.filter_by(status='activated').all()
        elif filter_status == 'deactivated':
            managers = Manager.query.filter_by(status='deactivated').all()
        else:  # 'all' or no filter
            managers = Manager.query.all()

        # Convert images to Base64 format for rendering
        for manager in managers:
            if manager.image:
                manager.image_base64 = f"data:image/jpeg;base64,{b64encode(manager.image).decode('utf-8')}"
            else:
                manager.image_base64 = None

        
        notification_check = check_notification(role, user_id)

        # Render the template with filtered managers
        return render_template(
            'managers.html',
            managers=managers,
            role=role,
            user_name=user.name,
            filter=filter_status,  # Pass the filter to the template
            **counts,
            encoded_image=image_data,
            notification_check=len(notification_check)
        )
    

    except Exception as e:
        flash(f"Error retrieving managers: {str(e)}", "danger")
        return render_template(
            'managers.html',
            managers=[],
            role=role,
            user_name=user.name,
            filter=filter_status,
            **counts,
            encoded_image=image_data
        )

###################################### Route for Edit Manager #########################################
@manager_bp.route('/edit/<int:manager_id>', methods=['GET', 'POST'])
def edit_manager(manager_id):
    manager = Manager.query.get_or_404(manager_id)
    user_id = session.get('user_id')
    role = session.get('role')
    image_data = get_image(role, user_id)
    user = get_user_query(role, user_id)

    if isinstance(role, bytes):
        role = role.decode('utf-8')
    # if isinstance(user_name, bytes):
    #     user_name = user_name.decode('utf-8')

    
    notification_check = check_notification(role, user_id)

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form.get('contact')
        password = request.form.get('password')
        image = request.files.get('image')  # Get the image from the form if provided

        # Validate if email already exists (excluding the current manager)
        existing_manager_email = Manager.query.filter(Manager.email == email, Manager.id != manager.id).first()
        if existing_manager_email:
            flash("The email is already in use by another manager.", "danger")
            return render_template('edit_manager.html', manager=manager, role=role, user_name=user.name,encoded_image=image_data)

        # Validate if contact already exists (excluding the current manager)
        existing_manager_contact = Manager.query.filter(Manager.contact == contact, Manager.id != manager.id).first()
        if existing_manager_contact:
            flash("The contact number is already in use by another manager.", "danger")
            return render_template('edit_manager.html', manager=manager, role=role, user_name=user.name,encoded_image=image_data)

        # Update manager details
        manager.name = name
        manager.email = email
        manager.contact = contact

        # If password is provided, hash and update it
        if password:
            manager.password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Handle image update if a new image is uploaded
        if image and allowed_file(image.filename):
            # Convert the image to binary data
            image_binary = image.read()
            manager.image = image_binary
            

        try:
            db.session.commit()


            create_notification(user_id=manager.id, 
                                role='Manager', 
                                notification_type='Edit', 
                                description=f'{user.name}, the Admin, has successfully edited the details of {manager.name}, the Manager.')

            flash('Manager updated successfully!', "success")
            return redirect(url_for('manager.get_managers'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating manager: {str(e)}", "danger")
    
    return render_template('edit_manager.html', 
                            manager=manager,
                            role=role,
                            user_name=user.name,
                            encoded_image=image_data,
                            notification_check=len(notification_check))


###################################### Route for Delete Manager #######################################
@manager_bp.route('/delete/<int:manager_id>', methods=['GET'])
def delete_manager(manager_id):
    manager = Manager.query.get_or_404(manager_id)
    role = session.get('role')
    user_id = session.get('user_id')
    user = get_user_query(role, user_id)

    try:
        manager.status = 'deactivated'
        # db.session.delete(manager)
        db.session.commit()

        create_notification(user_id=manager.id, 
                            role='Manager', 
                            notification_type='Delete', 
                            description=f'{user.name}, the Admin, has Deleted {manager.name}, the Manager.')


        flash("Manager deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting manager: {str(e)}", "danger")

    return redirect(url_for('manager.get_managers'))


###################################### Route for Lock/Unlock Manager ##################################
@manager_bp.route('/lock/<int:manager_id>', methods=['GET'])
def lock_manager(manager_id):
    role = session.get('role')
    user_id = session.get('user_id')
    user = get_user_query(role, user_id)
    manager = Manager.query.get_or_404(manager_id)

    try:
        if manager.status == 'activated':
            manager.status = 'deactivated'
            db.session.commit()

            create_notification(user_id=manager.id, 
                                role='Manager', 
                                notification_type='Lock', 
                                description=f'{user.name}, the Admin, has Locked {manager.name}, the Manager.')


            flash("Manager Locked successfully!", "danger")
        else:
            manager.status = 'activated'
            db.session.commit()

            create_notification(user_id=manager.id, 
                                role='Manager', 
                                notification_type='Unlock', 
                                description=f'{user.name}, the Admin, has Unlocked {manager.name}, the Manager.')

            flash("Manager Unlocked successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting manager: {str(e)}", "danger")

    return redirect(url_for('manager.get_managers'))


###################################### Route for Manager Profile ######################################
@manager_bp.route('/manager/<int:manager_id>', methods=['GET'])
def get_manager_profile(manager_id):
    try:
        # Query the manager by id
        manager = Manager.query.get_or_404(manager_id)

        return render_template('manager_profile.html', manager=manager)

    except Exception as e:
        flash(f"Error retrieving manager profile: {str(e)}", "danger")
        return redirect(url_for('manager.get_managers'))

###################################### Route for Manager Dashboard ####################################
@manager_bp.route('/', methods=['GET', 'POST'])
def manager_home():
    # Fetch session data
    user_name = session.get('user_name', 'User')
    role = session.get('role')
    user_id = session.get('user_id')
    image_data = get_image(role, user_id)

    # Initialize variables
    super_distributor_count, distributor_count, kitchen_count = 0, 0, 0
    total_sales_amount, total_orders_count, quantity_sold = 0, 0, 0
    sales_data, monthly_sales = [], []
    months, total_sales = [], []
    notification_check = None

    try:
        # Fetch data
        super_distributors = SuperDistributor.query.filter_by(manager_id=user_id).all()
        super_distributor_ids = [sd.id for sd in super_distributors]
        super_distributor_count = len(super_distributors)

        distributors = Distributor.query.filter(Distributor.super_distributor.in_(super_distributor_ids)).all()
        distributor_ids = [dist.id for dist in distributors]
        distributor_count = len(distributor_ids)

        all_kitchens = Kitchen.query.filter(Kitchen.distributor_id.in_(distributor_ids)).all()
        kitchen_ids = [kitchen.id for kitchen in all_kitchens]
        kitchen_count = len(all_kitchens)

        total_sales_amount = (
            db.session.query(db.func.sum(Order.total_amount))
            .join(Sales, Order.order_id == Sales.order_id)  # Join Sales model to filter orders
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
            .join(Sales, Order.order_id == Sales.order_id)  # Join Sales model to filter orders
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
            .order_by(Order.order_id.desc())
            .all()
        )

        notification_check = check_notification(role, user_id)

    except Exception as e:
        logging.error(f"Error fetching data: {e}")

    # Render template
    return render_template(
        'manager/manager_index.html',
        super_distributor_count=super_distributor_count,
        distributor_count=distributor_count,
        kitchen_count=kitchen_count,
        total_sales_amount=total_sales_amount,
        total_orders_count=total_orders_count,
        quantity_sold=quantity_sold,
        sales_data=sales_data,
        user_name=user_name,
        role=role,
        notification_check=len(notification_check),
        encoded_image=image_data,
        months=months,
        total_sales=total_sales,
        barChartData={"labels": months, "values": total_sales},
    )

###################################### Route for Manager Sales Report #################################


