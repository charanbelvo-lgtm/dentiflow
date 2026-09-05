"""Create missing DentiFlow tables without deleting or changing existing records."""
from app import app
from models import db

with app.app_context():
    db.create_all()
    print('DentiFlow tables verified.')
