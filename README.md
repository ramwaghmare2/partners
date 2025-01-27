#  Hierarchy Management System (FOOD_DELIVERY_HIERARCHY)

This project is a web-based Hierarchy Management System developed using Flask, SQLAlchemy, and MySQL. It helps manage hierarchical structures such as organizations, departments, and teams with user management, roles, and authentication features.  

## Features  

- User authentication (login, registration).
- Admin functionality for managing users.
- CRUD operations for managing hierarchical data (users).
- Role-based access control (admin, manager, super_distributor, distributor, kitchen).
- RESTful API for interacting with the system.

## Technologies Used

- Backend: Flask (Python web framework)
- Database: MySQL with SQLAlchemy ORM
- Password Hashing: bcrypt
- Migrations: Flask-Migrate
- Frontend: HTML, CSS ,JavaScript, Bootstrap (for simple frontend interface)

## Installation

### 1. Clone the repository

git https://github.com/ramwaghmare2/food_delivery_hierarchy
cd food_delivery_hierarchy

### 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

### 3. Install the required dependencies
pip install -r requirements.txt

### 4. Set up the database
Make sure MySQL is installed and running. Then, set up the database using Flask-Migrate.

# Make sure to configure your MySQL URI in `config.py`
flask db init      # Initialize the migration repository
flask db migrate   # Generate migration scripts
flask db upgrade   # Apply migrations to the database

### 5. Run the application
python app.py
The application will be available at http://127.0.0.1:5000/.

API Endpoints
1. User Registration
POST /user/signup: Registers a new user.
Required fields:select_role, name, email, contact, password ,confirm_password

2. User Login
POST /user/login: Logs in a user and returns a JWT token.
Required fields:select_role, email, password

3. Admin Routes
GET /admin/admin: Get admin profile.
admin Profile.
POST /admin/logout: To logout.
POST /user/profile-edit: To edit profile.
GET /user/delete/<int:user_id>:To delete user.
GET /wallet/all:TO get wallet details.

Acknowledgments
Flask - A micro web framework for Python
SQLAlchemy - Object Relational Mapper (ORM) for Python
MySQL - Database management system


This `README.md` provides an overview of your project, installation instructions, and API endpoints, which should help other developers understand the structure and how to get started. Adjust the paths and URLs based on your actual implementation.
