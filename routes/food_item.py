###################################### Importing Required Libraries ###################################
from flask import Blueprint, request, jsonify, render_template ,flash ,redirect,url_for,session
from utils.notification_service import check_notification, create_notification
from utils.services import allowed_file, get_image, get_user_query
from models import db, FoodItem ,Cuisine
from base64 import b64encode

###################################### Blueprint For Food Item ########################################
food_item_bp = Blueprint('food_item', __name__)

###################################### Route for Add Food Item ########################################
@food_item_bp.route('/add_food_item', methods=['GET', 'POST'])
def add_food_item():
    user_id = session.get('user_id')
    role = session.get('role')
    image_data = get_image(role, user_id)
    user = get_user_query(role, user_id)

    notification_check = check_notification(role, user_id)
    
    if request.method == 'POST':
        item_name = request.form['item_name']
        description = request.form['description']
        price = request.form['price']
        cuisine_id = request.form['cuisine_id']
        image = request.files.get('image')  # Get the image from the form

        if len(description.split()) > 30:
            flash('Description is too long, Wirte in 20 words!', 'danger')
            return redirect(url_for('food_item.add_food_item'))

        image_binary = None
        if image and allowed_file(image.filename):
            image_binary = image.read()
        
        try:
            new_food_item = FoodItem(
                item_name=item_name,
                description=description,
                price=price,
                cuisine_id=cuisine_id,
                kitchen_id=user_id,
                image=image_binary
            )
            db.session.add(new_food_item)
            db.session.commit()
            exception_message = f"Description is too long, Wirte in 20 words!"

            create_notification(user_id=user.id, 
                                role=role, 
                                notification_type='Add', 
                                description=f'{user.name}, the {role}, has Successfully Added {item_name}.')

            flash('Food item added successfully!', 'success')
            return redirect(url_for('food_item.add_food_item'))  # Redirect after successful POST
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'error')
    cuisines = Cuisine.query.all()  # Fetch all cuisines for the dropdown
    return render_template('add_food_item.html',
                           cuisines=cuisines,
                           user_id=user_id,
                           encoded_image=image_data,
                           user_name=user.name,
                           role=role,
                           notification_check=len(notification_check))


###################################### Create a New FoodItem ##########################################
@food_item_bp.route('/food_items/<int:kitchen_id>', methods=['GET'])
def get_food_items_by_kitchen(kitchen_id):
    user_id=session.get('user_id')
    role = session.get('role')
    image_data = get_image(role, user_id)
    user = get_user_query(role, user_id)
    notification_check = check_notification(role, user_id)
    # Query to get food items for the given kitchen_id
    food_items = FoodItem.query.filter_by(kitchen_id=kitchen_id).all()
    # Convert images to Base64 format
    for food in food_items:
            if food.image:
                food.image_base64 = f"data:image/jpeg;base64,{b64encode(food.image).decode('utf-8')}"
            else:
                food.image_base64 = None
    # Render the template with the food items
    return render_template('food_item.html',
                           food_items=food_items,
                           kitchen_id=kitchen_id,
                           user_id=user_id,
                           encoded_image=image_data,
                           user_name=user.name,
                           role=role,
                           notification_check=len(notification_check))

###################################### Update a FoodItem by ID ########################################
@food_item_bp.route('/food_items/edit/<int:id>', methods=['GET', 'POST'])
def edit_food_item(id):
    # Retrieve the food item by ID
    food_items = FoodItem.query.get_or_404(id)
    user_id= session.get('user_id')
    role = session.get('role')
    user = get_user_query(role, user_id)
    image_data = get_image(role, user_id)

    if request.method == 'POST':
        name = request.form.get('name')
        descrption = request.form.get('description')
        price = request.form.get('price')
        image = request.files.get('image')  # Get the image from the form

        image_binary = None
        if image and allowed_file(image.filename):
            image_binary = image.read()

        # Update food item with the form data
        food_items.item_name = name
        food_items.description = descrption
        food_items.price = price
        if image_binary:
            food_items.image = image_binary
        
        # Commit the changes to the database
        db.session.commit()

        create_notification(user_id=user.id, 
                                role=role, 
                                notification_type='Edit', 
                                description=f'{user.name}, the {role}, has Successfully edited {food_items.item_name}.')

        # Flash success message
        flash('Food item updated successfully!', 'success')
        
        return redirect(url_for('food_item.get_food_items_by_kitchen',kitchen_id=user_id))

    # If it's a GET request, render the edit form with the current data
    return render_template('edit_food_item.html',
                           food_items=food_items,
                           user_id=user_id,
                           role=role,
                           encoded_image=image_data,
                           user_name=user.name)

###################################### Delete a FoodItem by ID ########################################
@food_item_bp.route('/food_items/delete/<int:item_id>', methods=['GET'])
def delete_food_item(item_id):
    item = FoodItem.query.get_or_404(item_id)
    kitchen_id = item.kitchen_id
    user_id= session.get('user_id')
    role = session.get('role')
    user = get_user_query(role, user_id)

    # Delete the food item
    db.session.delete(item)
    db.session.commit()

    create_notification(user_id=user.id, 
                        role='Kitchen', 
                        notification_type='Delete', 
                        description=f'{user.name}, the {role}, has Deleted {item.item_name}.')

    flash('Food item deleted successfully', 'danger')
    return redirect(url_for('food_item.get_food_items_by_kitchen', kitchen_id=kitchen_id))
