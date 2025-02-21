###################################### Importing Required Libraries ###################################
from flask import Blueprint, request, jsonify, session, redirect, render_template, flash, current_app, url_for
from utils.notification_service import check_notification, create_notification
from werkzeug.security import check_password_hash, generate_password_hash
from utils.services import get_model_counts , get_image, get_user_query
from models import db, Kitchen, Distributor, FoodItem, Order, Sales, OrderItem, Payment
from datetime import datetime, timedelta
from utils.services import allowed_file
from pos_bill import generate_and_print_bill
from sqlalchemy import func
from base64 import b64encode
import bcrypt
import json
import base64

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
    kitchen_image = None
    notification_check = check_notification(role, user_id)
    if kitchen.image:
        kitchen_image = base64.b64encode(kitchen.image).decode('utf-8')

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
                           kitchen_image=kitchen_image,
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
    print("User ID ", user_id)
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


@kitchen_bp.route('/POS', methods=['GET', 'POST'])
def pos():
    role = session.get('role')
    user_id = session.get('user_id')
    user = get_user_query(role, user_id)
    image_data = get_image(role, user_id)
    notification_check = check_notification(role, user_id)
    food_items = FoodItem.query.filter(FoodItem.kitchen_id == user_id).all()
    for food in food_items:
        if food.image:
            food.image_base64 = f"data:image/jpeg;base64,{b64encode(food.image).decode('utf-8')}"
        else:
            food.image_base64 = None
    return render_template('kitchen/pos.html',
                           user_id=user_id,
                           user=user,
                           role=role,
                           user_name=user.name,
                           encoded_image=image_data,
                           notification_check=len(notification_check),
                           menu_items=food_items
                           )



@kitchen_bp.route('/POS-order', methods=['POST'])
def pos_order():
    try:
        user_id = session.get('user_id')
        if not user_id:
            raise ValueError("User not logged in.")
        
        # Get cart items and payment method from the request body
        data = request.get_json()
        if not data or 'cart_items' not in data or 'payment_method' not in data:
            raise ValueError("Cart items or payment method are missing.")

        cart_items = data['cart_items']
        payment_method = data['payment_method']
        
        if not cart_items:
            raise ValueError("Cart is empty.")
        
        kitchen_id = user_id
        if not kitchen_id:
            raise ValueError("Kitchen ID is required.")

        # Validate cart items
        total_amount = 0
        for item in cart_items:
            if 'item_id' not in item or not item['item_id'] or not str(item['item_id']).isdigit():
                raise ValueError("Invalid item ID in cart.")
            if 'quantity' not in item or not item['quantity'] or not str(item['quantity']).isdigit():
                raise ValueError("Invalid quantity in cart.")
            if 'price' not in item or not item['price']:
                raise ValueError("Invalid price in cart.")
            
            total_amount += float(item['price']) * int(item['quantity'])

        # Create the new order with the calculated total amount
        new_order = Order(
            kitchen_id=user_id,
            total_amount=total_amount,
            order_status='Pending'  # Set initial status to 'Pending'
        )
        db.session.add(new_order)
        db.session.commit()

        # Create and add order items to the database
        order_items_details = []
        for item in cart_items:
            food_item = FoodItem.query.get(item['item_id'])
            if not food_item:
                raise ValueError(f"FoodItem with id {item['item_id']} does not exist.")

            original_price = float(item['price'])  # Store the original price
            item_total_price = original_price * item['quantity']  # Calculate total price for this order item

            # Create the order item
            order_item = OrderItem(
                order_id=new_order.order_id,
                item_id=item['item_id'],
                quantity=item['quantity'],
                price=item_total_price,  # Save the total price
            )
            db.session.add(order_item)
            # Append the order item details to the list
            order_items_details.append({
                'item_id': item['item_id'],
                'quantity': item['quantity'],
                'item_price': original_price,
                'total_price': item_total_price
            })

        # Create the payment record
        payment = Payment(
            order_id=new_order.order_id,
            payment_method=payment_method,  # Store the selected payment method
            payment_status='Pending'  # Set payment status to 'Pending'
        )
        db.session.add(payment)
        db.session.commit()

        # Commit all changes and update the total amount of the order
        db.session.commit()
        order_items_details = [
            {
                'name': item.food_item.item_name,  # Include item name here
                #'item_id': str(item.id),
                'quantity': item.quantity,
                'price': item.food_item.price,  # Rename `item_price` to `price`
                'total_price': item.quantity * item.food_item.price
            }
            for item in OrderItem.query.filter_by(order_id=new_order.order_id).all()
        ]
        print("Order Item details",order_items_details)
        # Prepare order details
        order_details = {
            'order_id': new_order.order_id,
            'kitchen_name': new_order.kitchen.name,
            'total_amount': total_amount,
            #'order_items': order_items_details,  # Rename this to `items`
            'items': order_items_details,  # Ensures compatibility
            'payment_method': payment.payment_method if payment.payment_method else 'Not provided',
            'created_at': new_order.created_at.strftime('%Y-%m-%d %H:%M:%S'),  # Convert datetime
            'customer_name': "customer_name",  # Add this
            'address': "customer_address"  # Add this
        }
        # Debugging print to check if data is correct before calling bill generation
        print("Order details before bill generation:", order_details)

        # Call the function to generate and print the bill
        generate_and_print_bill(order_details)
        

        # Clear the cart from the session after placing the order
        session.pop(f'cart_{user_id}', None)

        # Return a JSON response with the order details
        return jsonify({
            'message': f'Order placed successfully! Order ID is {new_order.order_id}',
            'order_id': new_order.order_id,
            'total_amount': total_amount,
            'order_items': order_items_details,
            'payment_method': payment_method if payment_method else 'Not provided'  # Optionally return payment method
        }), 201

    except ValueError as ve:
        db.session.rollback()
        return jsonify({'error': str(ve)}), 400

    except KeyError as ke:
        db.session.rollback()
        return jsonify({'error': f'Missing key: {str(ke)}'}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
