###################################### Importing Required Libraries ###################################
import os

###################################### Configuration Class ############################################
class Config:

    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key')

    PARTNERS_DB = os.getenv('PARTNERS_DB_URL', 'mysql+pymysql://root:root@localhost/hierarchical_db')
    CUSTOMER_DB = os.getenv('CUSTOMER_DB_URL', 'mysql+pymysql://root:root@localhost/sample_fd')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_BINDS = {
        'partners_db': PARTNERS_DB,
        'customer_db': CUSTOMER_DB
    }

    CELERY_BROKER_URL = 'mysql+pymysql://root:root@localhost/hierarchical_db'  # Celery broker URL (could still be Redis/RabbitMQ, but MySQL for result backend)
    CELERY_RESULT_BACKEND = 'db+mysql://root:root@localhost/hierarchical_db'  # Use MySQL for the result backend (same as the main database)
    CELERY_ACCEPT_CONTENT = ['json']  # Celery will accept JSON formatted tasks
    CELERY_TASK_SERIALIZER = 'json'  # Serialize tasks in JSON format
