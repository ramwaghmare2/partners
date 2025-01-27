###################################### Importing Required Libraries ###################################
from flask import Blueprint, jsonify, request, render_template, redirect ,flash ,url_for, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Customer, db, FoodItem
from utils.helpers import handle_error
from werkzeug.security import check_password_hash, generate_password_hash
from base64 import b64encode

###################################### Blueprint For Customer ######################################### 
customer_bp = Blueprint('customer', __name__,template_folder='../templates/customer', static_folder='../templates/customer/static')

###################################### Route for Customer Dashboard ###################################
@customer_bp.route('/', methods=['GET'])
def customer_dashboard():

    food_items = FoodItem.query.all()
    for item in food_items:
        if item.image:
            item.image = b64encode(item.image).decode('utf-8')
            item.image = f"data:image/jpeg;base64,{item.image}"
    return render_template('index.html', food_items=food_items)


###################################### Route for Customer Registration ################################
@customer_bp.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'GET':
        return render_template('register.html')

    try:
        data = request.form  # Use form data from the HTML form
        name = data.get('name')
        email = data.get('email')
        contact = data.get('contact')
        password = generate_password_hash(data.get('password'))
        address = data.get('address')

        # Check if email already exists
        if Customer.query.filter_by(email=email).first():
            flash("Email already exists. Please use a different email.", "danger")
            return render_template('register.html')

        new_user = Customer(name=name, email=email, contact=contact, password=password, address=address)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return render_template('login.html')
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return render_template('register.html')


###################################### Route for Customer Login #######################################
@customer_bp.route('/login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'GET':
        return render_template('login.html')

    try:
        data = request.form
        login_id = data.get('contact') or data.get('email')
        password = data.get('password')

        user = Customer.query.filter(
            (Customer.contact == login_id) | (Customer.email == login_id)
        ).first()

        if not user or not check_password_hash(user.password, password):
            flash("Invalid email or password.", "danger")
            return render_template('login.html')

        #access_token = create_access_token(identity=user.id)
        session['user_id'] = user.id
        flash("You have logged in successfully.", "success")
        return redirect(url_for('customer.customer_dashboard'))
    except Exception as e:
        return handle_error(e)


###################################### Route for Customer Profile #####################################
@customer_bp.route('/profile', methods=['GET'])
def profile():
    try:
        #user_id = get_jwt_identity()
        #user = Customer.query.get(user_id)

        #if not user:
            #return jsonify({'message': 'User not found'}), 404

        return render_template('customer/profile.html') #user=user
    except Exception as e:
        return handle_error(e)

###################################### Route for Customer Logout ######################################
@customer_bp.route('/logout', methods=['GET'])
def logout_user():
    session.pop('user_id', None)
    flash('Logout Successful')
    return render_template('login.html')

###################################### Route for Customer Delete Account ##############################
@customer_bp.route('/delete', methods=['GET', 'POST'])
@jwt_required()
def delete_account():
    if request.method == 'GET':
        return render_template('customer/delete_account.html')

    try:
        data = request.form
        user_id = get_jwt_identity()
        user = Customer.query.get(user_id)

        if not user:
            return render_template('customer/delete_account.html', error="User not found.")
        
        if not check_password_hash(user.password, data['password']):
            return render_template('customer/delete_account.html', error="Invalid password.")

        user.status = 'deactivated'
        # db.session.delete(user)
        db.session.commit()
        return redirect('/customer/logout')
    except Exception as e:
        return handle_error(e)
    
    
###################################### Route for Customer Forgot Passowrd #############################
@customer_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('customer/forgot_password.html')

    try:
        data = request.form
        user = Customer.query.filter(
            (Customer.contact == data.get('contact')) | 
            (Customer.email == data.get('email'))
        ).first()

        if not user:
            return render_template('customer/forgot_password.html', error="User not found.")

        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if new_password != confirm_password:
            return render_template('customer/forgot_password.html', error="Passwords do not match.")

        user.password = generate_password_hash(new_password)
        db.session.commit()
        return redirect('/customer/login')
    except Exception as e:
        return handle_error(e)
