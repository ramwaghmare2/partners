###################################### Importing Required Libraries ###################################
from sqlalchemy import create_engine, MetaData, Table
from datetime import timedelta
import os

###################################### Configuration Class ############################################
class Config:

    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=5)  # Correct way to set session lifetime

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:root@localhost/FDHMSA')  # Database connection string for SQLAlchemy

    SQLALCHEMY_TRACK_MODIFICATIONS = False
"""engine = create_engine(SQLALCHEMY_DATABASE_URI)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    CELERY_BROKER_URL = 'mysql+pymysql://root:root@localhost/hierarchical_db'  # Celery broker URL (could still be Redis/RabbitMQ, but MySQL for result backend)
    CELERY_RESULT_BACKEND = 'db+mysql://root:root@localhost/hierarchical_db'  # Use MySQL for the result backend (same as the main database)
    CELERY_ACCEPT_CONTENT = ['json']  # Celery will accept JSON formatted tasks
    CELERY_TASK_SERIALIZER = 'json'  # Serialize tasks in JSON format"""
