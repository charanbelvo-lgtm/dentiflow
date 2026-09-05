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

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{quote_plus(MYSQL_USER)}:{quote_plus(MYSQL_PASSWORD)}@{MYSQL_HOST}:{MYSQL_PORT}/{quote_plus(MYSQL_DATABASE)}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', '0').lower() in {'1', 'true', 'yes'}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'uploads'))
