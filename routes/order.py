###################################### Importing Required Libraries ###################################
from models import Order, FoodItem, OrderItem, Sales, SuperDistributor, Distributor, Kitchen, Manager
from flask import Blueprint, request, jsonify, session, redirect, render_template, url_for, flash
from utils.notification_service import check_notification
from werkzeug.exceptions import NotFound
from datetime import datetime, timedelta
from utils.services import get_image
from models import FoodItem, Order
from models.order import db
from base64 import b64encode
from sqlalchemy import or_

###################################### Blueprint For Order ############################################
order_bp = Blueprint('order', __name__, static_folder='../static')

###################################### Route for Place Order ##########################################
@order_bp.route('/place-order/<int:item_id>', methods=['GET','POST'])
def place_order(item_id):
    try:

        data = request.form

        item = FoodItem.query.filter_by(id=item_id).first()
        if not item:
            raise ValueError(f"FoodItem with id {item_id} does not exist.")
        if item.image:
            item.image_base64 = f"data:image/jpeg;base64,{b64encode(item.image).decode('utf-8')}"
        else:
            item.image_base64 = None

        user_id = session.get('user_id')
        if not user_id:
            raise ValueError("User not logged in.")        

        if request.method == 'POST':
            total_amount = 0  # Initialize total amount to 0

            new_order = Order(
                user_id=user_id,
                kitchen_id=data['kitchen_id'],
                total_amount=total_amount,  # This will be updated after calculating
                order_status='Pending'  # Set initial status to 'Pending'
            )
            db.session.add(new_order)
            db.session.commit()

            order_items_details = []
                    
            menu_item = FoodItem.query.get(item_id)
            if not menu_item:
                raise ValueError(f"FoodItem with id {item_id} does not exist.")

            original_price = item.price   # Store the original price
            item_total_price = original_price * int(data['quantity'])  # Calculate total price for this order item base on quantity.
            
            # Create the order item
            order_item = OrderItem(
                order_id=new_order.order_id,
                item_id=item_id,
                quantity=data['quantity'],
                price=item_total_price,  # Save the original price
            )
            db.session.add(order_item)

            # Append the order item details to the list
            order_items_details.append({
                'item_id': item_id,
                'quantity': data['quantity'],
                'item_price': original_price,
                'total_price': item_total_price
            })

            # Add the item's total price to the total amount for the order
            total_amount += item_total_price
            total_amount_with_gst_and_delivery = total_amount# + gst + delivery_charge

            # Update the total amount of the order
            new_order.total_amount = total_amount_with_gst_and_delivery
            db.session.commit()
            
            flash('Order Successful!')
            return redirect(url_for('customer.customer_dashboard'))
    
        return render_template('order/place_order.html', item=item)

    except ValueError as ve:
        db.session.rollback()
        return jsonify({'error': str(ve)}), 400
    
    except KeyError as ke:
        db.session.rollback()
        return jsonify({'error': f"Missing key: {str(ke)}"}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


###################################### Route for Order Details ########################################
@order_bp.route('/<int:order_id>', methods=['GET'])
def get_order(order_id):
    try:
        order = Order.query.get_or_404(order_id) # Fetch the order 
        # Fetch Order details.
        order_data = {
            'order_id': order.order_id,
            'restaurant_id': order.restaurant_id,
            'user_id': order.user_id,
            'total_amount': order.total_amount,
            'status': order.order_status,
            # Fetch oredr item details.
            'items': [                              
                {'item_id': item.item_id, 'quantity': item.quantity}
                for item in order.order_items
            ]
        }
        
        return jsonify(order_data), 200
    
    except NotFound:
        # If order not found.
        return jsonify({'message': 'Order not found'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

###################################### Route for Order Details ########################################
@order_bp.route('/user/<int:user_id>', methods=['GET'])
def get_orders_by_user_id(user_id):
    try:
        orders = Order.query.filter_by(user_id=user_id).all()
        
        if not orders:
            return jsonify({'message': 'No orders yet'}), 200
        
        orders_data = [
            {
                'order_id': order.order_id,
                'restaurant_id': order.restaurant_id,
                'total_amount': order.total_amount,
                'status': order.order_status,
                'created_at': order.created_at,
                'updated_at': order.updated_at
            }
            for order in orders
        ]
        
        return jsonify(orders_data), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

###################################### Route for Order Details ########################################
@order_bp.route('/my-orders', methods=['GET'])
def get_orders_login_user():
    try:
        user_id = session.get('user_id')

        orders = Order.query.filter(
                                    Order.user_id == user_id, 
                                    Order.order_status.in_(['Processing', 'Pending', 'Completed'])
                                ).all()



        if not orders:
            flash('No orders yet')
            return redirect(url_for('customer.customer_dashboard'))

        # Prepare the orders data with order items to return
        orders_data = [
            {
                'order_id': order.order_id,
                'kitchen_id': order.kitchen.name,
                'total_amount': order.total_amount,
                'status': order.order_status,
                'created_at': order.created_at,
                'updated_at': order.updated_at,
                'items': [
                    {
                        'item_id': item.food_item.item_name,
                        'quantity': item.quantity,
                        'price': item.food_item.price,
                        'item_total_price': item.price,
                        'total_price': item.price * item.quantity
                    }
                    for item in order.order_items
                ]
            }
            for order in orders
        ]
        return render_template('order/my_orders.html', orders_data=orders_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

###################################### Method to Delete the Order along with Order items ##################################
@order_bp.route('/delete/<int:order_id>', methods=['GET'])
def cancel_order(order_id):
    try:
        # Fetch the order
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"message": "Order not found."}), 404  

        # Check if the order status is "Pending" or "Processing"
        if order.order_status not in ['Pending', 'Processing']:
            flash("Only orders with status 'Pending' or 'Processing' can be deleted.")
            # return jsonify({"message": "Only orders with status 'Pending' or 'Processing' can be deleted."}), 400
            return redirect(url_for('order.get_orders_login_user'))
        
        # Updated the order status
        order.order_status = 'Cancelled'
        db.session.commit()

        # Delete all related OrderItems
        # order_item = OrderItem.query.filter_by(order_id=order_id)
        # for order in order_item:
        #     order.order_status = 'Cancelled'
        #     db.session.commit()

        # return jsonify({"message": "Order deleted successfully!"}), 200
        flash('Order Cancelled successfully!')
        return redirect(url_for('order.get_orders_login_user'))  

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400  

###################################### Route for Order Cart ###########################################
@order_bp.route('/cart-order', methods=['GET', 'POST'])
def order_cart():
    
    try:
        user_id = session.get('user_id')
        if not user_id:
            raise ValueError("User not logged in.")

        cart_key = f'cart_{user_id}'
        cart_items = session.get(cart_key, [])
        if not cart_items:
            raise ValueError("Cart is empty.")
        
        data = request.form
    
        if request.method == 'POST':
            kitchen_id = data.get('kitchen_id')
            if not kitchen_id:
                raise ValueError("Kitchen ID is required.")
            if not kitchen_id.isdigit():
                raise ValueError("Invalid kitchen ID.")
            
            for item in cart_items:
                if 'item_id' not in item or not item['item_id'] or not str(item['item_id']).isdigit():
                    raise ValueError("Invalid item ID in cart.")
                if 'quantity' not in item or not item['quantity'] or not str(item['quantity']).isdigit():
                    raise ValueError("Invalid quantity in cart.")
                if 'price' not in item or not item['price']:
                    raise ValueError("Invalid price in cart.")    

            total_amount = 0  # Initialize total amount to 0

            # Create the new order with a default total_amount
            new_order = Order(
                user_id=user_id,
                kitchen_id=kitchen_id, 
                total_amount=total_amount,
                order_status='Pending'  # Set initial status to 'Pending'
            )
            db.session.add(new_order)
            db.session.commit()

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

                # Add the item's total price to the total amount for the order
                total_amount += item_total_price

            # Update the total amount of the order
            new_order.total_amount = total_amount
            db.session.commit()

            # Clear the cart from the session
            session.pop(cart_key, None)

            # return jsonify({
            #     'message': 'Order created successfully!',
            #     'order_id': new_order.order_id,
            #     'total_amount': total_amount,
            #     'address': user.address,
            #     'order_items': order_items_details
            # }), 201 

            # return redirect(url_for('payment.make_payment', order_id=new_order.order_id))
            flash('Order Placed Successfylly!')
            return redirect(url_for('customer.customer_dashboard'))

        from base64 import b64encode

        items_with_images = []
        for item in cart_items:
            food_item = FoodItem.query.get(item['item_id'])
            if food_item:
                food_image = food_item.image  # Assuming this is the binary data
                if food_image:  # Ensure there's image data
                    food_image_base64 = f"data:image/jpeg;base64,{b64encode(food_image).decode('utf-8')}"
                else:
                    food_image_base64 = None  # If no image data, set to None or a default placeholder
                
                items_with_images.append({
                    'item_id': food_item.id,
                    'name': food_item.item_name,  # Assuming there’s a name attribute
                    'price': food_item.price,
                    'quantity': item['quantity'],
                    'food_image': food_image_base64,  # Use base64 encoded image data
                    'kitchen_id': food_item.kitchen_id
                })
 
        
        return render_template('order/place_order_mul.html', items=items_with_images)
    
    except ValueError as ve:
        db.session.rollback()
        flash(f"Error: {str(ve)}")
        
    except KeyError as ke:
        db.session.rollback()
        flash(f'Error:  Missing key: {str(ke)}')
        return redirect(url_for('order.get_cart'))

    except Exception as e:
        db.session.rollback()
        flash(f'error: {str(e)}')
        return redirect(url_for('order.get_cart'))


###################################### Route for Kitchen Orders #######################################
@order_bp.route('/kitchen-order', methods=['GET', 'POST'])
def kitchen_orders( ):
    try:
        # Get the logged-in user's details
        user_id = session.get('user_id')
        role = session.get('role')
        user_name = session.get('user_name')
        image_data = get_image(role, user_id)
        notification_check = check_notification(role, user_id)
        if not user_id or not role:
            flash('Unauthorized access', 'error')
            return redirect(url_for('auth.login'))  # Redirect to the login page

        # Initialize query based on role
        if role == 'Distributor':
            distributor = Distributor.query.filter_by(user_id=user_id).first()
            if not distributor:
                flash('Unauthorized access', 'error')
                return redirect(url_for('auth.login'))
            kitchen_ids = [kitchen.id for kitchen in distributor.kitchens]
        
        elif role == 'SuperDistributor':
            super_distributor = SuperDistributor.query.filter_by(id=user_id).first()
            if not super_distributor:
                flash('Unauthorized access', 'error')
                return redirect(url_for('auth.login'))
            distributor_ids = [distributor.id for distributor in super_distributor.distributors]
            kitchens = Kitchen.query.filter(Kitchen.distributor_id.in_(distributor_ids)).all()
            kitchen_ids = [kitchen.id for kitchen in kitchens]

        elif role == 'Manager':
            manager = Manager.query.filter_by(id=user_id).first()
            if not manager:
                flash('Unauthorized access', 'error')
                return redirect(url_for('auth.login'))
            super_distributor_ids = [sd.id for sd in manager.super_distributors]
            distributors = Distributor.query.filter(Distributor.super_distributor.in_(super_distributor_ids)).all()
            distributor_ids = [distributor.id for distributor in distributors]
            kitchens = Kitchen.query.filter(Kitchen.distributor_id.in_(distributor_ids)).all()
            kitchen_ids = [kitchen.id for kitchen in kitchens]
                           
        elif role == 'Kitchen':
            kitchen_ids = [session.get('user_id')]  # Assuming the kitchen ID is stored in the session
        
        else:
            flash('Invalid role', 'error')
            return redirect(url_for('auth.login'))
        
        # Build the base query
        query = Order.query.filter(Order.kitchen_id.in_(kitchen_ids))

        # Apply filters based on query parameters
        order_status = request.args.get('status', 'All')
        if order_status and order_status != 'All':
            query = query.filter(Order.order_status == order_status)

        selected_kitchen_id = request.args.get('kitchen_id')
        if selected_kitchen_id and selected_kitchen_id != 'All':
            query = query.filter(Order.kitchen_id == int(selected_kitchen_id))
        
        date_filter = request.args.get('date', 'All')
        today = datetime.now()

        if date_filter == 'Today':
            start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Order.created_at >= start_date)
        
        elif date_filter == 'Yesterday':
            start_date = (today - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Order.created_at >= start_date, Order.created_at < end_date)
        
        elif date_filter == 'Weekly':
            start_date = today - timedelta(days=today.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Order.created_at >= start_date)
        
        elif date_filter == 'Monthly':
            start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Order.created_at >= start_date)
        
        elif date_filter == 'Yearly':
            start_date = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Order.created_at >= start_date)

        query = query.order_by(Order.created_at.desc())
        # Fetch the filtered orders
        orders = query.all()
        # return {"orders": [order.to_dict() for order in orders]}  # Assuming to_dict() is implemented
        # Prepare orders data for display
        print(orders)
        orders_data = [
            {
                'order_id': order.order_id,
                'kitchen_id': order.kitchen_id,
                'kitchen_name': order.kitchen.name,
                'total_amount': order.total_amount,
                'status': order.order_status,
                'customer_name': f"{order.customer.name}",
                'created_at': order.created_at,
                'updated_at': order.updated_at,
                'items': [
                    {
                        'item_id': item.item_id,
                        'item_name':item.food_item.item_name,
                        'quantity': item.quantity,
                        'price': item.food_item.price,
                        'item_total_price': item.price,
                        'total_price': item.price * item.quantity
                    }
                    for item in order.order_items
                ]
            }
            for order in orders
        ]

        return render_template('order/kitchen_order.html', 
                               user_id=user_id, 
                               orders_data=orders_data, 
                               user_name=user_name, 
                               role=role,
                               date_filter=date_filter,
                               selected_kitchen_id=selected_kitchen_id,
                               order_status=order_status,
                               encoded_image=image_data,
                               notification_check=len(notification_check)
                            )
    
    except Exception as e:
        flash({'error': str(e)})
        if role == 'SuperDistributor':
            return redirect(url_for('super_distributor.super_distributor'))
        else:
            return redirect(url_for('kitchen.kitchen_home'))
    
###################################### Route for Update Order Status ##################################
@order_bp.route('/update-status/<int:order_id>', methods=['GET'])
def update_status(order_id):
    try:
        user_id = session.get('user_id')
        order = Order.query.filter_by(order_id=order_id).first()
        order.order_status = 'Completed'
        db.session.commit()
        sales = Sales(
            order_id=order.order_id,
            cuisine_id=order.order_items[0].food_item.cuisine_id,
            kitchen_id=order.kitchen_id,
            item_id=order.order_items[0].item_id
        )
        db.session.add(sales)
        db.session.commit()

        flash('Order Status updated Successfully!', 'success')
        return redirect(url_for('order.kitchen_orders', kitchen_id=user_id))
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('order.kitchen_orders', kitchen_id=user_id))


###################################### Routes for Cart ################################################
@order_bp.route('/cart/<int:item_id>', methods=['GET', 'POST'])
def add_to_cart(item_id):

    item = FoodItem.query.filter_by(id=item_id).first()
    if item.image:
        item.image_base64 = f"data:image/jpeg;base64,{b64encode(item.image).decode('utf-8')}"
    else:   
        item.image_base64 = None

    user_id = session.get('user_id')

    if request.method == 'POST':
        
        try:
            
            data = request.form

            item_id = item_id
            quantity = data.get('quantity')  # Set default quantity to 1
            quantity = int(quantity)  # Ensure quantity is an integer

            if not item_id:
                flash('Item ID is required.')
                return redirect(url_for('customer.customer_dashboard'))

            # Fetch the item from the database
            food_item = FoodItem.query.get(item_id)
            if not food_item:
                flash('Item not found.')
                return redirect(url_for('customer.customer_dashboard'))

            price = food_item.price

            cart_key = f'cart_{user_id}'
            if cart_key not in session:
                session[cart_key] = []

            cart = session[cart_key]

            # Check if the item is already in the cart
            for cart_item in cart:
                if cart_item['item_id'] == item_id:
                    cart_item['quantity'] += quantity
                    break
            else:
                # If item is not in the cart, add it as a new entry
                cart.append({'item_id': item_id, 'quantity': quantity, 'price': price, 'Name': item.item_name})

            session[cart_key] = cart

            # return jsonify({'message': 'Item added to cart'}), 201
            flash('Item added to cart successfully.')
            return redirect(url_for('customer.customer_dashboard'))

        except Exception as e:
            flash(f"BadRequest Error: {str(e)}")
            return redirect(url_for('customer.customer_dashboard'))
        except Exception as e:
            flash(f"Unexpected Error: {str(e)}")
            redirect(url_for('customer.customer_dashboard'))
        
    # current_user = User.query.filter_by(user_id=user_id).first()
        
    return render_template('order/add_cart.html', item=item)

###################################### Route for View Cart ############################################
@order_bp.route('/cart', methods=['GET'])
def get_cart():
    try:
        # Retrieve the user ID from the JWT
        # user_id = get_jwt_identity()
        user_id = session.get('user_id')
        cart_key = f'cart_{user_id}'

        # Get the cart from the session, default to an empty list if not found
        cart = session.get(cart_key, [])
        
        if not cart:
            # return jsonify({'message': 'Cart is empty.'}), 200
            flash('Cart is empty.')
            return redirect(url_for('customer.customer_dashboard'))

        total_price = 0
        for item in cart:
            # Ensure quantity and price are numeric
            quantity = float(item.get('quantity', 0))  # Default to 0 if not present
            price = float(item.get('price', 0))  # Default to 0 if not present

            if not isinstance(quantity, (int, float)) or not isinstance(price, (int, float)):
                flash(f"Invalid quantity or price type: Quantity: {quantity}, Price: {price}")
                return redirect(url_for('customer.customer_dashboard'))

            total_price += quantity * price

        # return jsonify({'cart': cart, 'total_price': total_price}), 200

        return render_template('order/view_cart.html', cart=cart, total_price=total_price)
    
    except Exception as e:
        flash(f"Unexpected Error: {str(e)}")
        return redirect(url_for('customer.customer_dashboard'))
    
###################################### Route for Delete Cart ##########################################
@order_bp.route('/delete-cart/<int:item_id>', methods=['GET'])
def delete_item_cart(item_id):
    try:
        user_id = session.get('user_id')
        cart_key = f'cart_{user_id}'

        # Check if the cart exists and is not empty
        if cart_key not in session or not session[cart_key]:
            flash('Cart is empty.')
            return redirect(url_for('customer.customer_dashboard'))

        cart = session[cart_key]
        item_found = False

        # Find the item in the cart and remove it
        for cart_item in cart:
            if cart_item['item_id'] == item_id:
                cart.remove(cart_item)
                item_found = True
                session[cart_key] = cart
                flash('Item removed from cart.')
                return redirect(url_for('order.get_cart'))

        # If the item wasn't found
        if not item_found:
            flash('Item not found in cart.')
            return redirect(url_for('customer.get_cart'))

    except Exception as e:
        flash(f"Unexpected Error: {str(e)}")
        return redirect(url_for('ccustomer.customer_dashboard'))