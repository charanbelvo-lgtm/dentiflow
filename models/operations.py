from datetime import datetime
from . import db

class LabOrder(db.Model):
    __tablename__ = 'lab_orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(30), unique=True, nullable=False) # e.g. "LAB-2026-105"
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    lab_name = db.Column(db.String(100), nullable=False) # e.g. "DentCraft Precision Lab", "Apex Digital CAD/CAM"
    restoration_type = db.Column(db.String(50), nullable=False) # Zirconia Crown, Ceramic Inlay, Clear Aligner, Complete Denture, PFM Bridge, Implant Abutment
    tooth_numbers = db.Column(db.String(50), nullable=False) # e.g. "16, 17"
    shade = db.Column(db.String(20), default='A2 / Vita 3D')
    stage = db.Column(db.String(50), default='In Production') # Prescription, Sent to Lab, In Production, Quality Check, Ready, Delivered
    due_date = db.Column(db.Date, nullable=False)
    cost = db.Column(db.Float, default=2500.0)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient')
    doctor = db.relationship('Doctor')

    def to_dict(self):
        # Progress percentage
        stage_map = {
            'Prescription': 15,
            'Sent to Lab': 35,
            'In Production': 60,
            'Quality Check': 85,
            'Ready': 95,
            'Delivered': 100
        }
        return {
            'id': self.id,
            'order_number': self.order_number,
            'patient_id': self.patient_id,
            'patient_name': self.patient.name if self.patient else '',
            'doctor_name': self.doctor.name if self.doctor else '',
            'lab_name': self.lab_name,
            'restoration_type': self.restoration_type,
            'tooth_numbers': self.tooth_numbers,
            'shade': self.shade,
            'stage': self.stage,
            'progress_percent': stage_map.get(self.stage, 50),
            'due_date': self.due_date.strftime('%d %b %Y'),
            'cost': self.cost,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%d %b %Y')
        }

class Equipment(db.Model):
    __tablename__ = 'equipments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # e.g. "Dental Chair 01 (Anthos A3)", "Euronda Class B Autoclave", "Sirona Heliodent Plus RVG"
    category = db.Column(db.String(50), default='Operatory') # Operatory, Sterilization, Imaging, Lab, Compressor
    serial_number = db.Column(db.String(50), default='SN-9824201')
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    last_service_date = db.Column(db.Date, nullable=False)
    next_service_due = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), default='Operational') # Operational, Maintenance Due, Under Repair, Calibrated
    service_vendor = db.Column(db.String(100), default='Anthos MedTech Services')
    service_contact = db.Column(db.String(20), default='+91 98450 11223')

    def to_dict(self):
        days_to_service = (self.next_service_due - datetime.utcnow().date()).days
        is_overdue = days_to_service < 0
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'serial_number': self.serial_number,
            'last_service_date': self.last_service_date.strftime('%d %b %Y'),
            'next_service_due': self.next_service_due.strftime('%d %b %Y'),
            'days_to_service': days_to_service,
            'is_overdue': is_overdue,
            'status': 'Maintenance Due' if is_overdue else self.status,
            'service_vendor': self.service_vendor,
            'service_contact': self.service_contact
        }

class ReferralDoctor(db.Model):
    __tablename__ = 'referral_doctors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # e.g. "Dr. Vikram Mehta (ENT Specialist)"
    specialty = db.Column(db.String(100), default='ENT Surgeon / Physician')
    clinic_hospital = db.Column(db.String(150), default='Apollo Medical Center')
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    total_referred = db.Column(db.Integer, default=12)
    converted_count = db.Column(db.Integer, default=10)
    total_revenue_generated = db.Column(db.Float, default=145000.0)
    commission_paid = db.Column(db.Float, default=14500.0)

    def to_dict(self):
        conv_rate = round((self.converted_count / max(1, self.total_referred)) * 100, 1)
        return {
            'id': self.id,
            'name': self.name,
            'specialty': self.specialty,
            'clinic_hospital': self.clinic_hospital,
            'phone': self.phone,
            'email': self.email,
            'total_referred': self.total_referred,
            'converted_count': self.converted_count,
            'conversion_rate': conv_rate,
            'total_revenue_generated': self.total_revenue_generated,
            'commission_paid': self.commission_paid
        }

class FeedbackNPS(db.Model):
    __tablename__ = 'feedback_nps'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)
    score = db.Column(db.Integer, nullable=False) # 0 to 10
    category = db.Column(db.String(20), nullable=False) # Promoter (9-10), Passive (7-8), Detractor (0-6)
    comments = db.Column(db.Text, nullable=True)
    root_cause = db.Column(db.String(50), nullable=True) # Wait time, Pain / Discomfort, Billing, Communication, Doctor Behavior, Hygiene, None
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient')
    doctor = db.relationship('Doctor')

    def to_dict(self):
        return {
            'id': self.id,
            'patient_name': self.patient.name if self.patient else 'Anonymous',
            'doctor_name': self.doctor.name if self.doctor else 'Clinic Staff',
            'score': self.score,
            'category': self.category,
            'comments': self.comments,
            'root_cause': self.root_cause or 'N/A',
            'created_at': self.created_at.strftime('%d %b %Y')
        }

class Campaign(db.Model):
    __tablename__ = 'campaigns'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False) # e.g. "6-Month Cleaning Recall Drive"
    campaign_type = db.Column(db.String(50), nullable=False) # Birthday, Recall, Lapsed Win-back, Membership, Review Request
    target_audience = db.Column(db.String(150), nullable=False) # "Patients overdue by >180 days (48 patients)"
    channels = db.Column(db.String(50), default='WhatsApp + SMS')
    status = db.Column(db.String(50), default='Ready to Launch') # Ready to Launch, Active, Completed, Scheduled
    total_targeted = db.Column(db.Integer, default=45)
    sent_count = db.Column(db.Integer, default=0)
    engaged_count = db.Column(db.Integer, default=0)
    appointments_booked = db.Column(db.Integer, default=0)
    estimated_revenue = db.Column(db.Float, default=45000.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'campaign_type': self.campaign_type,
            'target_audience': self.target_audience,
            'channels': self.channels,
            'status': self.status,
            'total_targeted': self.total_targeted,
            'sent_count': self.sent_count,
            'engaged_count': self.engaged_count,
            'appointments_booked': self.appointments_booked,
            'estimated_revenue': self.estimated_revenue,
            'created_at': self.created_at.strftime('%d %b %Y')
        }
