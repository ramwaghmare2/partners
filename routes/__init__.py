###################################### Routes #########################################################
from .admin import admin_bp
from .customer import customer_bp
from .distributor import distributor_bp
from .kitchen import kitchen_bp
from .manager import manager_bp
from .super_distributor import super_distributor_bp
from .cuisine import cuisine_bp
from .order import order_bp
from .food_item import food_item_bp
from .dashboard import dashboard_bp
from .user_routes import user_bp
from .wallet import wallet_bp
from .royalty import royalty_bp
from .notification_routes import notification_bp
from .sales_report import sales_bp
from .orders_report import orders_bp

###################################### Function to Register Blueprints ################################
def create_app_routes(app):
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(distributor_bp, url_prefix='/distributor')
    app.register_blueprint(kitchen_bp, url_prefix='/kitchen')
    app.register_blueprint(manager_bp, url_prefix='/manager')
    app.register_blueprint(super_distributor_bp, url_prefix='/super_distributor')
    app.register_blueprint(cuisine_bp, url_prefix='/cuisine')
    app.register_blueprint(order_bp, url_prefix='/order')
    app.register_blueprint(food_item_bp, url_prefix='/fooditem')
    app.register_blueprint(sales_bp, url_prefix='/sales')  
    app.register_blueprint(orders_bp, url_prefix='/admin/orders')  
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(wallet_bp, url_prefix='/wallet')
    app.register_blueprint(royalty_bp, url_prefix='/royalty')
    app.register_blueprint(notification_bp, url_prefix='/notification')
