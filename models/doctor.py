from datetime import datetime
from . import db

class Branch(db.Model):
    __tablename__ = 'branches'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(50), default='Bengaluru')
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    is_main = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    chairs = db.relationship('Chair', backref='branch', lazy=True)
    doctors = db.relationship('Doctor', backref='branch', lazy=True)
    users = db.relationship('User', backref='branch', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'address': self.address,
            'city': self.city,
            'phone': self.phone,
            'email': self.email,
            'is_main': self.is_main,
            'is_active': self.is_active,
            'chair_count': len(self.chairs) if self.chairs else 0,
            'doctor_count': len(self.doctors) if self.doctors else 0
        }

class Chair(db.Model):
    __tablename__ = 'chairs'

    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    chair_number = db.Column(db.String(20), nullable=False) # e.g. "Chair 01"
    name = db.Column(db.String(100), default='Dental Operatory')
    status = db.Column(db.String(50), default='Available') # Available, In Treatment, Cleaning, Patient Waiting, Maintenance
    current_patient = db.Column(db.String(100), nullable=True)
    current_doctor = db.Column(db.String(100), nullable=True)
    current_procedure = db.Column(db.String(100), nullable=True)
    session_start_time = db.Column(db.DateTime, nullable=True)
    equipment_specs = db.Column(db.String(255), default='Anthos A3 Plus + Sirona X-Ray')

    def to_dict(self):
        elapsed_min = 0
        if self.session_start_time and self.status == 'In Treatment':
            elapsed_min = int((datetime.utcnow() - self.session_start_time).total_seconds() / 60)
        return {
            'id': self.id,
            'branch_id': self.branch_id,
            'chair_number': self.chair_number,
            'name': self.name,
            'status': self.status,
            'current_patient': self.current_patient,
            'current_doctor': self.current_doctor,
            'current_procedure': self.current_procedure,
            'elapsed_minutes': elapsed_min,
            'equipment_specs': self.equipment_specs
        }

class Doctor(db.Model):
    __tablename__ = 'doctors'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100), nullable=False) # Endodontist, Orthodontist, Periodontist, Oral Surgeon, Prosthodontist, General Dentist
    degree = db.Column(db.String(100), default='BDS, MDS')
    registration_no = db.Column(db.String(50), default='KDC-28492-A')
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(255), default='/static/img/cartoon-doctor.svg')
    assigned_chair = db.Column(db.String(50), default='Chair 01')
    experience_years = db.Column(db.Integer, default=8)
    consultation_fee = db.Column(db.Float, default=500.0)
    commission_rate = db.Column(db.Float, default=30.0) # 30% revenue share
    rating = db.Column(db.Float, default=4.9)
    is_active = db.Column(db.Boolean, default=True)
    color_badge = db.Column(db.String(20), default='#2563EB')

    # Relationships
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)
    shifts = db.relationship('StaffShift', backref='doctor', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'branch_id': self.branch_id,
            'name': self.name,
            'specialty': self.specialty,
            'degree': self.degree,
            'registration_no': self.registration_no,
            'phone': self.phone,
            'email': self.email,
            'avatar': self.avatar,
            'assigned_chair': self.assigned_chair,
            'experience_years': self.experience_years,
            'consultation_fee': self.consultation_fee,
            'commission_rate': self.commission_rate,
            'rating': self.rating,
            'is_active': self.is_active,
            'color_badge': self.color_badge,
            'branch_name': self.branch.name if self.branch else 'Downtown Dental'
        }

class StaffShift(db.Model):
    __tablename__ = 'staff_shifts'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    shift_type = db.Column(db.String(50), default='Full Day') # Morning (9am-2pm), Evening (2pm-8pm), Full Day (9am-8pm), Leave, Half Day
    status = db.Column(db.String(50), default='Working') # Working, On Leave, Half Day, Unavailable
    notes = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'doctor_id': self.doctor_id,
            'doctor_name': self.doctor.name if self.doctor else '',
            'date': self.date.strftime('%Y-%m-%d') if self.date else '',
            'shift_type': self.shift_type,
            'status': self.status,
            'notes': self.notes
        }

class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='Approved') # Pending, Approved, Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'doctor_id': self.doctor_id,
            'doctor_name': self.doctor.name if self.doctor else '',
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'reason': self.reason,
            'status': self.status
        }
