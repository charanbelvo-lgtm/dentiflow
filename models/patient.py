from datetime import datetime
from . import db

class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(20), unique=True, nullable=False, index=True) # e.g. "DF-2026-001"
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False) # Male, Female, Other
    phone = db.Column(db.String(20), nullable=False, index=True)
    email = db.Column(db.String(100), nullable=True)
    blood_group = db.Column(db.String(10), default='B+')
    address = db.Column(db.String(255), nullable=True)
    emergency_contact_name = db.Column(db.String(100), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    primary_doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    avatar = db.Column(db.String(255), default='/static/img/cartoon-patient.svg')
    abdm_health_id = db.Column(db.String(50), nullable=True) # e.g. rahul.mehta@abdm
    insurance_policy_no = db.Column(db.String(50), nullable=True)
    insurance_provider = db.Column(db.String(100), nullable=True) # Star Health, HDFC ERGO, etc.
    outstanding_balance = db.Column(db.Float, default=0.0)
    total_spent = db.Column(db.Float, default=0.0)
    last_visit = db.Column(db.DateTime, nullable=True)
    next_appointment = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    primary_doctor = db.relationship('Doctor', backref='patients')
    branch = db.relationship('Branch', backref='patients')
    medical_alerts = db.relationship('MedicalAlert', backref='patient', cascade='all, delete-orphan', lazy=True)
    family_members = db.relationship('FamilyMember', foreign_keys='FamilyMember.patient_id', backref='patient', cascade='all, delete-orphan', lazy=True)
    documents = db.relationship('PatientDocument', backref='patient', cascade='all, delete-orphan', lazy=True)
    appointments = db.relationship('Appointment', backref='patient', lazy=True)
    tooth_findings = db.relationship('ToothFinding', backref='patient', cascade='all, delete-orphan', lazy=True)
    periodontal_records = db.relationship('PeriodontalRecord', backref='patient', cascade='all, delete-orphan', lazy=True)
    prescriptions = db.relationship('Prescription', backref='patient', cascade='all, delete-orphan', lazy=True)
    treatment_plans = db.relationship('TreatmentPlan', backref='patient', cascade='all, delete-orphan', lazy=True)
    invoices = db.relationship('Invoice', backref='patient', cascade='all, delete-orphan', lazy=True)
    xrays = db.relationship('XRayImage', backref='patient', cascade='all, delete-orphan', lazy=True)
    clinical_notes = db.relationship('ClinicalNote', backref='patient', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        alerts = [a.alert_text for a in self.medical_alerts if a.is_critical]
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'phone': self.phone,
            'email': self.email,
            'blood_group': self.blood_group,
            'address': self.address,
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'primary_doctor_id': self.primary_doctor_id,
            'primary_doctor_name': self.primary_doctor.name if self.primary_doctor else 'Dr. Ananya Sharma',
            'branch_id': self.branch_id,
            'branch_name': self.branch.name if self.branch else 'Downtown Dental',
            'avatar': self.avatar,
            'abdm_health_id': self.abdm_health_id,
            'insurance_policy_no': self.insurance_policy_no,
            'insurance_provider': self.insurance_provider,
            'outstanding_balance': self.outstanding_balance,
            'total_spent': self.total_spent,
            'last_visit_formatted': self.last_visit.strftime('%d %b %Y') if self.last_visit else 'Never',
            'next_appointment_formatted': self.next_appointment.strftime('%d %b %Y, %I:%M %p') if self.next_appointment else 'None scheduled',
            'critical_alerts': alerts,
            'created_at': self.created_at.strftime('%d %b %Y') if self.created_at else ''
        }

class MedicalAlert(db.Model):
    __tablename__ = 'medical_alerts'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    alert_type = db.Column(db.String(50), default='Allergy') # Allergy, Condition, Medication, Bleeding Disorder, Pregnancy
    alert_text = db.Column(db.String(255), nullable=False) # e.g. "ALLERGY: Penicillin", "Hypertension", "Diabetic (Type 2)"
    is_critical = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'alert_type': self.alert_type,
            'alert_text': self.alert_text,
            'is_critical': self.is_critical
        }

class FamilyMember(db.Model):
    __tablename__ = 'family_members'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    relation = db.Column(db.String(50), nullable=False) # Spouse, Child, Parent, Sibling
    phone = db.Column(db.String(20), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    linked_patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'name': self.name,
            'relation': self.relation,
            'phone': self.phone,
            'age': self.age,
            'linked_patient_id': self.linked_patient_id
        }

class PatientDocument(db.Model):
    __tablename__ = 'patient_documents'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    doc_type = db.Column(db.String(50), default='Consent Form') # Consent Form, Medical Report, Insurance Card, ID Proof
    file_url = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.String(20), default='1.2 MB')
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'title': self.title,
            'doc_type': self.doc_type,
            'file_url': self.file_url,
            'file_size': self.file_size,
            'upload_date': self.upload_date.strftime('%d %b %Y')
        }
