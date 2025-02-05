###################################### Importing Required Libraries ###################################
from flask import Blueprint, request, jsonify ,render_template,flash,redirect,url_for,session
from models import db, Cuisine
from utils.notification_service import check_notification, create_notification
from utils.services import get_image, get_user_query, allowed_file
from base64 import b64encode

###################################### Blueprint For Cuisine ##########################################
cuisine_bp = Blueprint('cuisine', __name__ , static_folder='../static')

###################################### Route for Add Cuisine's ########################################
@cuisine_bp.route('/cuisine', methods=['GET', 'POST'])
def add_cuisine():
    role = session.get('role')
    user_id = session.get('user_id')
    image_data = get_image(role ,user_id)
    user = get_user_query(role, user_id)
    notification_check = check_notification(role, user_id)
    if request.method == 'POST':
        
        # Get the form data
        name = request.form.get('name')
        description = request.form.get('description', '')  # Optional field
        image = request.files.get('image')
        print(image,'image')

        image_binary = None
        if image and allowed_file(image.filename):
            image_binary = image.read()
        
        # Check if the cuisine already exists
        existing_cuisine = Cuisine.query.filter_by(name=name).first()
        if existing_cuisine:
            flash('Cuisine already exists!','danger')
            return redirect(url_for('cuisine.add_cuisine'))
        
        # Create a new Cuisine object
        new_cuisine = Cuisine ( name = name,
                                description = description,
                                image = image_binary)
        
        try:
            # Add and commit to the database
            db.session.add(new_cuisine)
            db.session.commit()

            create_notification(user_id=user.id, 
                                role=role, 
                                notification_type='Add', 
                                description=f'{user.name}, the {role}, has Successfully Added {new_cuisine.name}.')

            flash('Cuisine added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')
        
        return redirect(url_for('cuisine.add_cuisine'))
    # Render the template for GET requests
    return render_template('cuisines/add_cuisine.html',
                           user_id=user_id,
                           role=role,
                           user_name=user.name,
                           encoded_image=image_data,
                           notification_check=len(notification_check))

 ###################################### Route for Display All Cuisine #######################################   
@cuisine_bp.route('/all-cuisines',methods=['POST','GET'])
def all_cuisines():
    role = session.get('role')
    user_id = session.get('user_id')
    image_data = get_image(role ,user_id)
    user = get_user_query(role, user_id)
    notification_check = check_notification(role, user_id)

    cuisines = Cuisine.query.order_by(Cuisine.id).all()
    for cuisine in cuisines:
        if cuisine.image:
            cuisine.image_base64 = f"data:image/jpeg;base64,{b64encode(cuisine.image).decode('utf-8')}"
        else:
            cuisine.image_base64 = None

    return render_template('cuisines/list_cuisines.html',
                           user_id=user_id,
                           cuisines=cuisines,
                           role=role,
                           user_name=user.name,
                           encoded_image=image_data,
                           notification_check=len(notification_check))

###################################### Route for Edit Cuisine #######################################
@cuisine_bp.route('/edit/<int:id>', methods=['POST','GET'])
def edit_cuisine(id):
    # Retrieve the food item by ID
    cuisines = Cuisine.query.get_or_404(id)
    user_id= session.get('user_id')
    role = session.get('role')
    user = get_user_query(role, user_id)
    image_data = get_image(role, user_id)

    if request.method == 'POST':
        name = request.form.get('name')
        descrption = request.form.get('description')
        image = request.files.get('image')  # Get the image from the form
        print(image)
        image_binary = None
        if image and allowed_file(image.filename):
            image_binary = image.read()

        # Update food item with the form data
        cuisines.name = name
        cuisines.description = descrption
        if image_binary:
            cuisines.image = image_binary
        
        # Commit the changes to the database
        db.session.commit()

        create_notification(user_id=user.id, 
                                role=role, 
                                notification_type='Edit', 
                                description=f'{user.name}, the {role}, has Successfully edited {cuisines.name}.')

        # Flash success message
        flash('Cuisine updated successfully!', 'success')
        
        return redirect(url_for('cuisine.all_cuisines'))

    # If it's a GET request, render the edit form with the current data
    return render_template('cuisines/edit_cuisines.html',
                           cuisine=cuisines,
                           user_id=user_id,
                           role=role,
                           encoded_image=image_data,
                           user_name=user.name)


###################################### Route for Delete Cuisine #######################################
@cuisine_bp.route('/cuisine/delete/<int:id>', methods=['POST','GET'])
def delete_cuisine(id):
    user_id = session.get('user_id')
    role = session.get('role')
    user = get_user_query(role, user_id)
    cuisine = Cuisine.query.get_or_404(id)
    try:
        db.session.delete(cuisine)
        db.session.commit()

        create_notification(user_id=user.id, 
                                role=role, 
                                notification_type='Delete', 
                                description=f'{user.name}, the {role}, has Successfully deleted {cuisine.name}.')

        flash('Cuisine deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'error')
    return redirect(url_for('cuisine.all_cuisines'))

