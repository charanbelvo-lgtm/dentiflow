from datetime import datetime
from . import db

class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    appointment_number = db.Column(db.String(20), unique=True, nullable=False) # e.g. "APT-1082"
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    chair_id = db.Column(db.Integer, db.ForeignKey('chairs.id'), nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    
    appointment_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(10), nullable=False) # e.g. "09:30 AM"
    duration_minutes = db.Column(db.Integer, default=30)
    procedure_name = db.Column(db.String(100), nullable=False) # e.g. "Root Canal", "Cleaning"
    
    status = db.Column(db.String(50), default='Confirmed') 
    # Confirmed, Waiting, In Treatment, Completed, Delayed, Cancelled, No-Show, Requested
    
    booking_source = db.Column(db.String(50), default='Walk-in') # Walk-in, Google, Instagram, WhatsApp, Referral, Online Portal
    deposit_amount = db.Column(db.Float, default=0.0)
    reminder_preference = db.Column(db.String(50), default='WhatsApp + SMS')
    notes = db.Column(db.Text, nullable=True)
    is_emergency = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to token
    token = db.relationship('QueueToken', backref='appointment', uselist=False, cascade='all, delete-orphan')
    chair = db.relationship('Chair', backref='appointments')

    def to_dict(self):
        return {
            'id': self.id,
            'appointment_number': self.appointment_number,
            'patient_id': self.patient_id,
            'patient_name': self.patient.name if self.patient else 'Unknown',
            'patient_phone': self.patient.phone if self.patient else '',
            'patient_avatar': self.patient.avatar if self.patient else '',
            'doctor_id': self.doctor_id,
            'doctor_name': self.doctor.name if self.doctor else 'Dr. Sharma',
            'doctor_avatar': self.doctor.avatar if self.doctor else '',
            'chair_id': self.chair_id,
            'chair_name': self.chair.chair_number if self.chair else 'Chair 01',
            'branch_id': self.branch_id,
            'appointment_date': self.appointment_date.strftime('%Y-%m-%d') if self.appointment_date else '',
            'start_time': self.start_time,
            'duration_minutes': self.duration_minutes,
            'procedure_name': self.procedure_name,
            'status': self.status,
            'booking_source': self.booking_source,
            'deposit_amount': self.deposit_amount,
            'reminder_preference': self.reminder_preference,
            'notes': self.notes,
            'is_emergency': self.is_emergency,
            'token_number': self.token.token_number if self.token else None,
            'created_at': self.created_at.strftime('%d %b %Y, %I:%M %p') if self.created_at else ''
        }

class QueueToken(db.Model):
    __tablename__ = 'queue_tokens'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    token_number = db.Column(db.String(20), nullable=False) # e.g. "Token #014"
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    chair_id = db.Column(db.Integer, db.ForeignKey('chairs.id'), nullable=True)
    procedure_name = db.Column(db.String(100), nullable=False)
    
    status = db.Column(db.String(50), default='Waiting') # Waiting, Serving, Completed, Skipped
    is_emergency = db.Column(db.Boolean, default=False)
    estimated_wait_min = db.Column(db.Integer, default=15)
    called_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    patient = db.relationship('Patient', backref='queue_tokens')
    doctor = db.relationship('Doctor', backref='queue_tokens')
    chair = db.relationship('Chair', backref='queue_tokens')

    def to_dict(self):
        return {
            'id': self.id,
            'appointment_id': self.appointment_id,
            'patient_id': self.patient_id,
            'patient_name': self.patient.name if self.patient else 'Unknown',
            'patient_phone': self.patient.phone if self.patient else '',
            'patient_avatar': self.patient.avatar if self.patient else '',
            'token_number': self.token_number,
            'doctor_id': self.doctor_id,
            'doctor_name': self.doctor.name if self.doctor else 'Dr. Sharma',
            'chair_id': self.chair_id,
            'chair_name': self.chair.chair_number if self.chair else 'Chair 01',
            'procedure_name': self.procedure_name,
            'status': self.status,
            'is_emergency': self.is_emergency,
            'estimated_wait_min': self.estimated_wait_min,
            'called_at': self.called_at.strftime('%I:%M %p') if self.called_at else None,
            'created_at': self.created_at.strftime('%I:%M %p') if self.created_at else ''
        }

class Waitlist(db.Model):
    __tablename__ = 'waitlists'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)
    preferred_date = db.Column(db.Date, nullable=False)
    preferred_time_range = db.Column(db.String(50), default='Morning (9am - 1pm)')
    procedure_name = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='Pending') # Pending, Offered, Booked, Expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient', backref='waitlist_entries')
    doctor = db.relationship('Doctor', backref='waitlist_entries')

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'patient_name': self.patient.name if self.patient else '',
            'patient_phone': self.patient.phone if self.patient else '',
            'doctor_name': self.doctor.name if self.doctor else 'Any Doctor',
            'preferred_date': self.preferred_date.strftime('%Y-%m-%d'),
            'preferred_time_range': self.preferred_time_range,
            'procedure_name': self.procedure_name,
            'notes': self.notes,
            'status': self.status
        }
