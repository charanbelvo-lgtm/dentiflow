import os
import pymysql
from dotenv import load_dotenv
from app import create_app
from models import db
from seed import seed_database

def setup():
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(BASE_DIR, '.env'))

    host = os.environ.get('MYSQL_HOST', 'localhost')
    port = int(os.environ.get('MYSQL_PORT', 3306))
    user = os.environ.get('MYSQL_USER', 'root')
    password = os.environ.get('MYSQL_PASSWORD', '')
    database = os.environ.get('MYSQL_DATABASE', 'dentiflow')

    print(f"Connecting to MySQL server at {host}:{port} as '{user}'...")
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=password)
        cursor = conn.cursor()
        print(f"Creating database '{database}' if not exists...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database};")
        conn.commit()
        cursor.close()
        conn.close()
        print("Database created or already exists.")
    except Exception as e:
        print(f"Failed to connect to MySQL: {e}")
        print("Please check your .env credentials and ensure MySQL is running.")
        return

    app = create_app()
    with app.app_context():
        print("Creating tables...")
        db.create_all()
        print("Seeding demo data without deleting existing records...")
        seed_database()
        print("Setup complete! You can now run `python app.py`.")

if __name__ == '__main__':
    setup()
