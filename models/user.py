from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='receptionist') # admin, doctor, receptionist, assistant, accountant
    avatar = db.Column(db.String(255), default='/static/img/cartoon-doctor.svg')
    phone = db.Column(db.String(20), nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    doctor_profile = db.relationship('Doctor', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'avatar': self.avatar,
            'phone': self.phone,
            'branch_id': self.branch_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    user_role = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    module = db.Column(db.String(50), nullable=False) # Clinical, Billing, Patient, Inventory, Settings
    ip_address = db.Column(db.String(45), default='127.0.0.1')
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_name': self.user_name,
            'user_role': self.user_role,
            'action': self.action,
            'module': self.module,
            'ip_address': self.ip_address,
            'details': self.details,
            'time_formatted': self.created_at.strftime('%I:%M %p, %d %b %Y') if self.created_at else '',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
