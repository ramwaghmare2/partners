###################################### Importing Required Libraries ###################################
from flask_sqlalchemy import SQLAlchemy

###################################### Database Configuration #########################################
db = SQLAlchemy()

###################################### Imporing Models ################################################
from .activitylog import ActivityLog
from .admin import Admin
from .cuisine import Cuisine
from .customer import Customer
from . delivery import Delivery
from .distributor import Distributor
from .food_item import FoodItem
from .kitchen import Kitchen
from .manager import Manager
from .notification import Notification
from .order_item import OrderItem
from .order import Order
from .payment import Payment
from .review import Review
from .royalty import RoyaltySettings
from .royalty import RoyaltyWallet
from .super_distributor import SuperDistributor
from .sales import Sales
