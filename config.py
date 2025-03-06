###################################### Importing Required Libraries ###################################
from sqlalchemy import create_engine, MetaData, Table
from datetime import timedelta
from pymongo import MongoClient
import os

###################################### Configuration Class ############################################
class Config:

    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=5)  # Correct way to set session lifetime

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:root@localhost/FDHMSA')  # Database connection string for SQLAlchemy

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configure POS Printer (Replace with your printer's Vendor ID and Product ID)
    VENDOR_ID = 0x04B8  
    PRODUCT_ID = 0x0202  
    
