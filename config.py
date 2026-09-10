import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Config:
    APP_ENV = os.environ.get('APP_ENV', 'development').lower()
    DEBUG = os.environ.get('FLASK_DEBUG', '0').lower() in {'1', 'true', 'yes'}
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if APP_ENV == 'production' and not SECRET_KEY:
        raise RuntimeError('SECRET_KEY must be set in production.')
    SECRET_KEY = SECRET_KEY or 'local-development-only-secret'
    
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'dentiflow')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    if APP_ENV == 'production' and MYSQL_HOST.lower() in {'localhost', '127.0.0.1'}:
        raise RuntimeError('MYSQL_HOST must be the private production MySQL hostname.')

    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = db_url
    elif os.environ.get('MYSQL_HOST') and os.environ.get('MYSQL_PASSWORD'):
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{quote_plus(MYSQL_USER)}:{quote_plus(MYSQL_PASSWORD)}@{MYSQL_HOST}:{MYSQL_PORT}/{quote_plus(MYSQL_DATABASE)}"
    elif APP_ENV == 'production':
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{quote_plus(MYSQL_USER)}:{quote_plus(MYSQL_PASSWORD)}@{MYSQL_HOST}:{MYSQL_PORT}/{quote_plus(MYSQL_DATABASE)}"
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'dentiflow.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', '0').lower() in {'1', 'true', 'yes'}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'uploads'))

    # Firebase Configuration
    FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY', '')
    FIREBASE_AUTH_DOMAIN = os.environ.get('FIREBASE_AUTH_DOMAIN', '')
    FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID', '')
    FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', '')
    FIREBASE_MESSAGING_SENDER_ID = os.environ.get('FIREBASE_MESSAGING_SENDER_ID', '')
    FIREBASE_APP_ID = os.environ.get('FIREBASE_APP_ID', '')
    FIREBASE_MEASUREMENT_ID = os.environ.get('FIREBASE_MEASUREMENT_ID', '')
    FIREBASE_SERVICE_ACCOUNT_PATH = os.environ.get(
        'FIREBASE_SERVICE_ACCOUNT_PATH', 
        os.path.join(BASE_DIR, 'firebase-service-account.json')
    )
