###################################### Importing Required Libraries ###################################
import os

###################################### Configuration Class ############################################
class Config:
    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://root:root@localhost/hierarchical_db')  # Database connection string for SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Secret Key for Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')

    # Celery Configuration
    CELERY_BROKER_URL = 'mysql+pymysql://root:root@localhost/hierarchical_db'  # Celery broker URL (could still be Redis/RabbitMQ, but MySQL for result backend)
    CELERY_RESULT_BACKEND = 'db+mysql://root:root@localhost/hierarchical_db'  # Use MySQL for the result backend (same as the main database)
    CELERY_ACCEPT_CONTENT = ['json']  # Celery will accept JSON formatted tasks
    CELERY_TASK_SERIALIZER = 'json'  # Serialize tasks in JSON format
