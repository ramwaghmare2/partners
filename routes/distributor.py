###################################### Importing Required Libraries ###################################
from flask import Blueprint, redirect, render_template, url_for, request, flash, session, current_app
from utils.services import get_model_counts, allowed_file ,get_image, get_user_query
from utils.notification_service import check_notification, create_notification
from models import db, SuperDistributor  ,Order ,OrderItem ,Sales, FoodItem
from models.distributor import Distributor
from models.kitchen import Kitchen
from datetime import datetime, timedelta
from base64 import b64encode
from sqlalchemy import func
import bcrypt
import json
import logging

###################################### Blueprint For Distributor ######################################
distributor_bp = Blueprint('distributor', __name__, template_folder='../templates/distributor', static_folder='../static')

###################################### Route for distributor dashboard ################################
@distributor_bp.route('/', methods=['GET', 'POST'])
def distributor_home():
    user_id = session.get('user_id')
    role = session.get('role')
    image_data = get_image(role, user_id)
    user = get_user_query(role, user_id)
    try:
        # Logging session data for debugging
        logging.debug(f"Session user_id: {session.get('user_id')}")

        # Get the logged-in distributor's ID from the session
        if not user_id:
            flash({'error': 'Unauthorized access'})
            logging.debug("Redirecting due to missing user_id in session")
            return redirect(url_for('distributor.distributor_home'))

        # Get the filter type (if any)
        filter_type = request.args.get('filter', 'today')

        # Fetch all active kitchens under this distributor
        kitchens = Kitchen.query.filter_by(distributor_id=user_id, status="activated").all()

        # Fetch orders based on the selected filter
        kitchen_ids = [kitchen.id for kitchen in kitchens]
        query = Order.query.filter(Order.kitchen_id.in_(kitchen_ids))

        orders = query.all()

        total_sales_data = db.session.query(
            Sales.sale_id,
            Sales.datetime,
            FoodItem.item_name,
            OrderItem.price,
            OrderItem.quantity,
            Order.order_id
        ).join(Order, Sales.order_id == Order.order_id) \
        .join(OrderItem, Order.order_id == OrderItem.order_id) \
        .join(FoodItem, OrderItem.item_id == FoodItem.id) \
        .filter(Order.kitchen_id.in_(kitchen_ids))

        # Order by datetime for recent sales first
        total_sales_data = total_sales_data.order_by(Sales.datetime.asc()).all()

        # Query to calculate total quantity sold
        total_quantity_sold = db.session.query(
            func.sum(OrderItem.quantity).label('total_quantity')
        ).join(Order, OrderItem.order_id == Order.order_id) \
        .filter(Order.kitchen_id.in_(kitchen_ids))

        #if start_date and end_date:
            #total_quantity_sold = total_quantity_sold.filter(Sales.datetime.between(start_date, end_date))

        # Fetch total quantity sold
        total_quantity_sold = total_quantity_sold.scalar()

        # Prepare data for the table
        kitchen_sales = {kitchen.name: 0 for kitchen in kitchens}
        for order in orders:
            kitchen = next(k for k in kitchens if k.id == order.kitchen_id)
            kitchen_sales[kitchen.name] += float(order.total_amount)  # Sum up the sales for each kitchen

        # Count of active kitchens for the logged-in distributor
        kitchen_count = len(kitchens)

        # Fetch orders for these active kitchens
        kitchen_ids = [kitchen.id for kitchen in kitchens]
        orders = Order.query.filter(Order.kitchen_id.in_(kitchen_ids)).all()

        # Count of orders related to the active kitchens
        order_count = len(orders)

        # Total price of all orders related to the active kitchens
        total_price = (
            db.session.query(func.sum(Order.total_amount))
            .join(Sales, Order.order_id == Sales.order_id)  # Join with Sales model
            .filter(Order.kitchen_id.in_(kitchen_ids))  # Filter by kitchen_ids
            .scalar()
        )
        total_price = float(total_price) if total_price else 0 # Convert to float

        # Prepare data for bar chart
        kitchen_order_count = {kitchen.name: 0 for kitchen in kitchens}
        kitchen_sales = {kitchen.name: 0 for kitchen in kitchens}

        for order in orders:
            kitchen = next(k for k in kitchens if k.id == order.kitchen_id)
            kitchen_order_count[kitchen.name] += 1
            kitchen_sales[kitchen.name] += float(order.total_amount)  # Convert to float

        # Prepare data for pie chart: Total sales amount for each kitchen
        kitchen_sales_total = {kitchen.name: 0 for kitchen in kitchens}
        
        # Calculate the total sales amount for each kitchen based on orders
        for order in orders:
            if order.order_status == 'Completed':
                kitchen = next(k for k in kitchens if k.id == order.kitchen_id)
                kitchen_sales_total[kitchen.name] += float(order.total_amount)  # Sum up the total sales amount

        
        notification_check = check_notification(role, user_id)

        # Render the distributor home page with table and chart data
        return render_template(
            'd_index.html', 
            user_name=user.name,
            role=role, 
            encoded_image=image_data,
            kitchen_count=kitchen_count,
            order_count=order_count,
            total_price=total_price,
            kitchen_names=json.dumps(list(kitchen_order_count.keys())),
            order_counts=json.dumps(list(kitchen_order_count.values())),
            sales_data=json.dumps(list(kitchen_sales.values())),
            pie_chart_labels=json.dumps(list(kitchen_sales_total.keys())),
            pie_chart_data=json.dumps(list(kitchen_sales_total.values())),
            kitchens=kitchens,
            kitchen_sales=kitchen_sales,
            filter_type=filter_type,
            total_sales_data=total_sales_data,
            total_quantity_sold=total_quantity_sold,
            notification_check=len(notification_check)
        )
    except Exception as e:
        flash({'error': str(e)})
        logging.error(f"Error occurred: {str(e)}")
        return redirect(url_for('distributor.distributor_home'))


###################################### Route for display all distributor ##############################
@distributor_bp.route('/all-distributor', methods=['GET'])
def all_distributor():
    role = session.get('role')
    user_id = session.get('user_id')
    image_data = get_image(role, user_id)
    counts = get_model_counts()
    user = get_user_query(role, user_id)

    # Get filter status from request parameters
    filter_status = request.args.get('status', 'all').lower()

    # Base query initialization
    query = Distributor.query

    if role == 'Admin':
        # Admin sees all distributors
        pass  # No additional filters for Admin
    elif role == 'SuperDistributor':
        # SuperDistributor sees their own distributors
        query = query.filter_by(super_distributor=user_id)
    else:
        # Other roles see distributors linked to their super distributors
        super_distributors = SuperDistributor.query.filter_by(manager_id=user_id).all()
        super_distributor_ids = [sd.id for sd in super_distributors]
        query = query.filter(Distributor.super_distributor.in_(super_distributor_ids))

    # Apply status filter
    if filter_status == 'activated':
        query = query.filter_by(status='activated')
    elif filter_status == 'deactivated':
        query = query.filter_by(status='deactivated')

    # Execute the final query
    all_distributors = query.all()

    # Convert images to Base64 format
    for distributor in all_distributors:
        if distributor.image:
            distributor.image_base64 = f"data:image/jpeg;base64,{b64encode(distributor.image).decode('utf-8')}"
        else:
            distributor.image_base64 = None

    notification_check = check_notification(role, user_id)

    return render_template(
        'd_all_distributor.html',
        total_distributors_count=len(all_distributors),
        all_distributors=all_distributors,
        role=role,
        user_name=user.name,
        encoded_image=image_data,
        filter=filter_status,
        notification_check=len(notification_check)
    )

###################################### Route to display all kitchens ##################################
@distributor_bp.route('/all-kitchens', methods=['GET'])
def distrubutor_all_kitchens():
    role = session.get('role')
    user_id = session.get('user_id')
    image_data = get_image(role, user_id)
    user = get_user_query(role, user_id)
    counts = get_model_counts()

    # Get filter status from request parameters
    filter_status = request.args.get('status', 'all').lower()

    # Base query initialization
    query = Kitchen.query

    if role == 'Admin':
        # Admin sees all kitchens
        pass  # No additional filters for Admin
    elif role == 'SuperDistributor':
        # SuperDistributor sees kitchens of their distributors
        distributors = Distributor.query.filter_by(super_distributor=user_id).all()
        distributor_ids = [dist.id for dist in distributors]
        query = query.filter(Kitchen.distributor_id.in_(distributor_ids))
    elif role == 'Distributor':
        # Distributor sees their own kitchens
        query = query.filter_by(distributor_id=user_id)
    else:
        # Other roles see kitchens linked to their distributors via super distributors
        super_distributors = SuperDistributor.query.filter_by(manager_id=user_id).all()
        super_distributor_ids = [sd.id for sd in super_distributors]
        distributors = Distributor.query.filter(Distributor.super_distributor.in_(super_distributor_ids)).all()
        distributor_ids = [dist.id for dist in distributors]
        query = query.filter(Kitchen.distributor_id.in_(distributor_ids))

    # Apply status filter
    if filter_status == 'activated':
        query = query.filter_by(status='activated')
    elif filter_status == 'deactivated':
        query = query.filter_by(status='deactivated')

    # Execute the final query
    all_kitchens = query.all()
    kitchens_count = len(all_kitchens)

    all_kitchen_ids = [kitchen.id for kitchen in all_kitchens]
    sales_by_kitchen = Sales.query.filter(Sales.kitchen_id.in_(all_kitchen_ids)).all()

    # Extract all order_ids from the sales data
    order_ids = [sale.order_id for sale in sales_by_kitchen]
    
    # Get Orders data based on the order_ids
    orders = Order.query.filter(Order.order_id.in_(order_ids)).all()

    # Helper function to calculate total sales for a given list of kitchens
    def calculate_total_sales(kitchens_list):
        total_sales = 0
        for kitchen in kitchens_list:
            # Find the sales corresponding to this kitchen
            kitchen_sales = [sale for sale in sales_by_kitchen if sale.kitchen_id == kitchen.id]
            
            # Collect orders related to these sales
            kitchen_orders = [order for order in orders if order.order_id in [sale.order_id for sale in kitchen_sales]]
            
            # Sum the total amount of orders for this kitchen
            total_sales += sum(order.total_amount for order in kitchen_orders)
        return total_sales
    
    # Convert images to Base64 format
    for kitchen in all_kitchens:
        if kitchen.image:
            kitchen.image_base64 = f"data:image/jpeg;base64,{b64encode(kitchen.image).decode('utf-8')}"
        else:
            kitchen.image_base64 = None
    
    # Create kitchen data with sales included
    kitchen_data = [
        {
            'id': kitchen.id,
            'name': kitchen.name,
            'distributor_name': kitchen.distributors.name if kitchen.distributors else 'N/A',
            'total_sales': calculate_total_sales([kitchen]),
            'image': kitchen.image_base64,
            'email': kitchen.email,
            'contact': kitchen.contact,
            'status': kitchen.status,

        }
        for kitchen in all_kitchens
    ]

    
    notification_check = check_notification(role, user_id)

    return render_template(
        'kitchen/all_kitchens.html',
        all_kitchens=kitchen_data,
        role=role,
        user_name=user.name,
        **counts,
        encoded_image=image_data,
        kitchens_count=kitchens_count,
        filter=filter_status,
        notification_check=len(notification_check)
    )


###################################### Route for delete the distributor ###############################
@distributor_bp.route('/delete/<int:distributor_id>', methods=['GET', 'POST'])
def delete_distributor(distributor_id):
    user_id = session.get('user_id')
    role = session.get('role')
    user = get_user_query(role, user_id)
    
    distributor = Distributor.query.get_or_404(distributor_id)

    try:
        distributor.status = 'deactivated'
        # db.session.delete(distributor)
        db.session.commit()

        create_notification(user_id=distributor.id, 
                            role='Distributor', 
                            notification_type='Delete', 
                            description=f'{user.name}, the {role}, has successfully Deleted Distributor, {distributor.name}.')


        flash("Distributor deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting manager: {str(e)}", "danger")

    return redirect(url_for('distributor.all_distributor'))


###################################### Route for lock the distributor #################################
@distributor_bp.route('/lock/<int:distributor_id>', methods=['GET'])
def lock_distributor(distributor_id):
    user_id = session.get('user_id')
    role = session.get('role')
    user = get_user_query(role, user_id)
    distributor = Distributor.query.get_or_404(distributor_id)

    try:
        if distributor.status == 'activated':
            distributor.status = 'deactivated'
            db.session.commit()

            create_notification(user_id=distributor.id, 
                                role='Distributor', 
                                notification_type='Lock', 
                                description=f'{user.name}, the {role}, has Locked {distributor.name}, the Distributor.')

            flash("Distributor Locked successfully!", "danger")
        else:
            distributor.status = 'activated'
            db.session.commit()

            create_notification(user_id=distributor.id, 
                                role='Distributor', 
                                notification_type='Unlock', 
                                description=f'{user.name}, the {role}, has Unlocked {distributor.name}, the Distributor.')

            flash("Distributor Unlocked successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error : {str(e)}", "danger")

    return redirect(url_for('distributor.all_distributor'))


###################################### Function for image storage #####################################
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

###################################### Route for edit the distributor #################################
@distributor_bp.route('/edit/<int:distributor_id>', methods=['GET', 'POST'])
def edit_distributor(distributor_id):
    distributor = Distributor.query.get_or_404(distributor_id)

    role = session.get('role')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 
    user = get_user_query(role, user_id)
    notification_check = check_notification(role, user_id)
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form.get('contact')
        password = request.form['password']
        image = request.files.get('image')  # Get the image from the form if it exists

        # Validate if email already exists (excluding the current distributor)
        existing_distributor_email = Distributor.query.filter(Distributor.email == email, Distributor.id != Distributor.id).first()
        if existing_distributor_email:
            flash("The email is already in use by another Distributor.", "danger")
            return render_template('edit_distributor.html', distributor=distributor, role=role)

        # Validate if contact already exists (excluding the current distributor)
        existing_distributor_contact = Distributor.query.filter(Distributor.contact == contact, Distributor.id != Distributor.id).first()
        if existing_distributor_contact:
            flash("The contact number is already in use by another Distributor.", "danger")
            return render_template('edit_distributor.html', distributor=distributor, role=role)

        # Update distributor details
        distributor.name = name
        distributor.email = email
        distributor.contact = contact

        # If password is provided, hash and update it
        if password:
            distributor.password = bcrypt.generate_password_hash(password).decode('utf-8')

        if image and allowed_file(image.filename):
            # Convert the image to binary data
            image_binary = image.read()
            distributor.image = image_binary

        try:
            db.session.commit()

            create_notification(user_id=distributor.id, 
                                role='Distributor', 
                                notification_type='Edit', 
                                description=f'{user.name}, the {role}, has Successfully Edited {distributor.name}, the Distributor.')


            flash("Distributor updated successfully!", "success")
            return redirect(url_for('distributor.all_distributor'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating Distributor: {str(e)}", "danger")
            return render_template('edit_distributor.html', distributor=distributor, role=role , encoded_image = image_data, user_name=user.name)

    return render_template('edit_distributor.html',
                           distributor=distributor,
                           role=role,
                           encoded_image=image_data,
                           user_name=user.name,
                           notification_check=len(notification_check))


###################################### Route for Display orders related to distributor ################
@distributor_bp.route('/distributor-orders', methods=['GET'])
def distributor_orders():
    try:
        # Get the logged-in distributor's ID from the session
        distributor_id = session.get('user_id')
        role = session.get('role')
        image_data= get_image(role, distributor_id)
        user = get_user_query(role, distributor_id) 
        if not distributor_id:
            flash({'error': 'Unauthorized access'})
            return redirect(url_for('distributor.distributor_home'))

        # Fetch all kitchens under this distributor
        kitchens = Kitchen.query.filter_by(distributor_id=distributor_id).all()
        kitchen_ids = [kitchen.id for kitchen in kitchens]

        # Get filter values from the query parameters
        selected_kitchen_id = request.args.get('kitchen_id')
        order_status = request.args.get('status', 'All')
        date_filter = request.args.get('date', 'All')

        # Start building the query
        query = Order.query.filter(Order.kitchen_id.in_(kitchen_ids))

        # Filter by selected kitchen
        if selected_kitchen_id and selected_kitchen_id != "All":
            query = query.filter(Order.kitchen_id == int(selected_kitchen_id))

        # Filter by order status
        if order_status and order_status != "All":
            query = query.filter(Order.order_status == order_status)

        # Filter by date range
        if date_filter != "All":
            today = datetime.now()
            if date_filter == "Today":
                start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Order.created_at >= start_date)
            elif date_filter == "Yesterday":
                start_date = (today - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Order.created_at >= start_date, Order.created_at < end_date)
            elif date_filter == "Weekly":
                start_date = today - timedelta(days=today.weekday())
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Order.created_at >= start_date)
            elif date_filter == "Monthly":
                start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Order.created_at >= start_date)
            elif date_filter == "Yearly":
                start_date = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Order.created_at >= start_date)

        query = query.order_by(Order.created_at.desc())
        orders = query.all()

        # Prepare order data for rendering
        orders_data = [
            {
                'order_id': order.order_id,
                'user_id': order.user_id,
                'kitchen_id': order.kitchen_id,
                'total_amount': order.total_amount,
                'status': order.order_status,
                'kitchen_name': order.kitchen.name,
                'customer_name': f"{order.customer.name}",
                'created_at': order.created_at,
                'updated_at': order.updated_at,
                'items': [
                    {
                        'item_id': item.item_id,
                        'item_name':item.food_item.item_name,
                        'quantity': item.quantity,
                        'price': item.price,
                        'total_price': item.price * item.quantity
                    }
                    for item in order.order_items
                ]
            }
            for order in orders
        ]

        notification_check = check_notification(role, distributor_id)

        # Render the distributor's order page
        return render_template(
            'distributor/d_orders.html',
            role=role,
            distributor_id=distributor_id,
            kitchens=kitchens,
            orders_data=orders_data,
            selected_kitchen_id=selected_kitchen_id,
            order_status=order_status,
            date_filter=date_filter,
            encoded_image=image_data,
            notification_check=len(notification_check)
        )
    
    except Exception as e:
        flash({'error': str(e)})
        return redirect(url_for('distributor.distributor_home'))


###################################### Route for view details of distributor ##########################
@distributor_bp.route('/view-details/<int:user_id>', methods=['GET'])
def view_details(user_id):
    id = session.get('user_id')
    role = session.get('role')
    user_name = get_user_query(role, id)
    encoded_image = get_image(role, id)
    
    # Get Distributors for the manager
    user = Distributor.query.filter_by(id=user_id).first()
    
    # Get Kitchens for the Distributors
    kitchens = Kitchen.query.filter(Kitchen.distributor_id == user.id).all()
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

    # Create kitchen data with sales included
    kitchen_data = [
        {
            'kitchen_name': kitchen.name,
            'distributor_name': kitchen.distributors.name,
            'total_sales': calculate_total_sales([kitchen])
        }
        for kitchen in kitchens
    ]

    details = 'Distributor'

    notification_check = check_notification(role, id)

    return render_template('view_details.html',
                           role=role,
                           user_name=user_name.name,
                           encoded_image=encoded_image,
                           user=user,
                           details=details,
                           kitchens=kitchen_data,
                           notification_check=len(notification_check)
                           )

