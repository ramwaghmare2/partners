###################################### Importing Required Libraries ###################################
from sqlalchemy import create_engine
from datetime import timedelta
from pymongo import MongoClient
import os


engine = create_engine(
    os.environ.get('DATABASE_URL', 'mysql+pymysql://root:root@localhost/FDHMSA'),
    pool_size=10,  # ✅ Maximum 10 connections in the pool
    max_overflow=5,  # ✅ Allow up to 5 extra connections
    pool_recycle=1800,  # ✅ Recycle connections every 30 minutes
    pool_pre_ping=True  # ✅ Check connections before using
)

###################################### Function to Get Database Connection (for raw queries) ###########
def get_db_connection():
    return engine.connect()

###################################### Configuration Class ############################################
class Config:

    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=5)  # Correct way to set session lifetime

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:root@localhost/FDHMSA')  # Database connection string for SQLAlchemy

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configure POS Printer (Replace with your printer's Vendor ID and Product ID)
    VENDOR_ID = 0x04B8  
    PRODUCT_ID = 0x0202  
    
