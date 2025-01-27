###################################### Importing Required Libraries ###################################
from flask import Blueprint, request, jsonify ,render_template,flash,redirect,url_for,session
from models import db, Cuisine
from utils.notification_service import check_notification, create_notification
from utils.services import get_image, get_user_query

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
        
        # Check if the cuisine already exists
        existing_cuisine = Cuisine.query.filter_by(name=name).first()
        if existing_cuisine:
            flash('Cuisine already exists!','danger')
            return redirect(url_for('cuisine.add_cuisine'))
        
        # Create a new Cuisine object
        new_cuisine = Cuisine(name=name,description=description)
        
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
    cuisines = Cuisine.query.order_by(Cuisine.id).all()
    # Render the template for GET requests
    return render_template('add_cuisine.html',
                           cuisines=cuisines,
                           role=role,
                           user_name=user.name,
                           encoded_image=image_data,
                           notification_check=len(notification_check))

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
    return redirect(url_for('cuisine.add_cuisine'))

