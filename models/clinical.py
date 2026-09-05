from datetime import datetime
from . import db

class ToothFinding(db.Model):
    __tablename__ = 'tooth_findings'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    tooth_number = db.Column(db.Integer, nullable=False) # FDI: 11-18, 21-28, 31-38, 41-48
    status = db.Column(db.String(50), default='Healthy') # Healthy, Cavity, Filling, Crown, Root Canal, Missing, Extraction, Implant, Watch
    surfaces = db.Column(db.String(50), default='') # M, O, D, B, L, MOD
    diagnosis = db.Column(db.String(255), nullable=True) # e.g. "Dental Caries on occlusal surface"
    recommended_treatment = db.Column(db.String(255), nullable=True) # e.g. "Composite Filling"
    estimated_cost = db.Column(db.Float, default=0.0)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    doctor = db.relationship('Doctor')

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'tooth_number': self.tooth_number,
            'status': self.status,
            'surfaces': self.surfaces,
            'diagnosis': self.diagnosis or 'Healthy tooth structure',
            'recommended_treatment': self.recommended_treatment or 'None',
            'estimated_cost': self.estimated_cost,
            'doctor_name': self.doctor.name if self.doctor else 'Dr. Sharma',
            'updated_at': self.updated_at.strftime('%d %b %Y') if self.updated_at else ''
        }

class PeriodontalRecord(db.Model):
    __tablename__ = 'periodontal_records'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    tooth_number = db.Column(db.Integer, nullable=False)
    pocket_depth_mb = db.Column(db.Integer, default=2) # Mesiobuccal (1-9 mm)
    pocket_depth_b = db.Column(db.Integer, default=2)  # Buccal
    pocket_depth_db = db.Column(db.Integer, default=2) # Distobuccal
    pocket_depth_ml = db.Column(db.Integer, default=2) # Mesiolingual
    pocket_depth_l = db.Column(db.Integer, default=2)  # Lingual
    pocket_depth_dl = db.Column(db.Integer, default=2) # Distolingual
    bleeding_on_probing = db.Column(db.Boolean, default=False)
    mobility = db.Column(db.String(10), default='0') # 0, I, II, III
    gingival_margin = db.Column(db.Integer, default=0) # mm recession
    furcation = db.Column(db.String(10), default='None') # None, Class I, Class II, Class III
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        max_depth = max(self.pocket_depth_mb, self.pocket_depth_b, self.pocket_depth_db,
                        self.pocket_depth_ml, self.pocket_depth_l, self.pocket_depth_dl)
        is_abnormal = max_depth >= 4 or self.bleeding_on_probing or self.mobility != '0'
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'tooth_number': self.tooth_number,
            'pocket_depth_mb': self.pocket_depth_mb,
            'pocket_depth_b': self.pocket_depth_b,
            'pocket_depth_db': self.pocket_depth_db,
            'pocket_depth_ml': self.pocket_depth_ml,
            'pocket_depth_l': self.pocket_depth_l,
            'pocket_depth_dl': self.pocket_depth_dl,
            'max_depth': max_depth,
            'bleeding_on_probing': self.bleeding_on_probing,
            'mobility': self.mobility,
            'gingival_margin': self.gingival_margin,
            'furcation': self.furcation,
            'is_abnormal': is_abnormal,
            'recorded_at': self.recorded_at.strftime('%d %b %Y')
        }

class Prescription(db.Model):
    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True)
    rx_number = db.Column(db.String(30), unique=True, nullable=False) # e.g. "RX-2026-089"
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    diagnosis = db.Column(db.String(255), nullable=True)
    general_advice = db.Column(db.Text, nullable=True) # e.g. "Warm salt water rinse 3x daily"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    doctor = db.relationship('Doctor')
    items = db.relationship('PrescriptionItem', backref='prescription', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'rx_number': self.rx_number,
            'patient_id': self.patient_id,
            'patient_name': self.patient.name if self.patient else '',
            'doctor_id': self.doctor_id,
            'doctor_name': self.doctor.name if self.doctor else '',
            'doctor_degree': self.doctor.degree if self.doctor else 'BDS, MDS',
            'doctor_reg': self.doctor.registration_no if self.doctor else 'KDC-28492-A',
            'diagnosis': self.diagnosis,
            'general_advice': self.general_advice,
            'date_formatted': self.created_at.strftime('%d %b %Y'),
            'items': [item.to_dict() for item in self.items]
        }

class PrescriptionItem(db.Model):
    __tablename__ = 'prescription_items'

    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=False)
    medicine_name = db.Column(db.String(100), nullable=False) # e.g. "Amoxicillin 500mg"
    dosage = db.Column(db.String(50), default='1 Capsule')
    frequency = db.Column(db.String(50), default='Thrice daily (TDS)') # 1-0-1, 1-1-1, Twice daily, Once daily
    duration = db.Column(db.String(50), default='5 days')
    instructions = db.Column(db.String(150), default='After food') # Before food, After food, As needed

    def to_dict(self):
        return {
            'id': self.id,
            'medicine_name': self.medicine_name,
            'dosage': self.dosage,
            'frequency': self.frequency,
            'duration': self.duration,
            'instructions': self.instructions
        }

class XRayImage(db.Model):
    __tablename__ = 'xray_images'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False) # e.g. "Full Mouth OPG", "Tooth #16 RVG"
    xray_type = db.Column(db.String(50), default='OPG') # OPG, RVG, Bitewing, Before/After, CBCT
    image_url = db.Column(db.String(255), nullable=False)
    comparison_image_url = db.Column(db.String(255), nullable=True) # For Before/After compare
    ai_cavity_detected = db.Column(db.Boolean, default=False)
    ai_bone_loss_detected = db.Column(db.Boolean, default=False)
    ai_periapical_lesion = db.Column(db.Boolean, default=False)
    ai_confidence = db.Column(db.Float, default=94.2)
    ai_analysis_notes = db.Column(db.Text, nullable=True)
    captured_date = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'title': self.title,
            'xray_type': self.xray_type,
            'image_url': self.image_url,
            'comparison_image_url': self.comparison_image_url,
            'ai_cavity_detected': self.ai_cavity_detected,
            'ai_bone_loss_detected': self.ai_bone_loss_detected,
            'ai_periapical_lesion': self.ai_periapical_lesion,
            'ai_confidence': self.ai_confidence,
            'ai_analysis_notes': self.ai_analysis_notes or 'AI Analysis indicates localized radiolucency on coronal margin. Dentist confirmation advised.',
            'captured_date': self.captured_date.strftime('%d %b %Y')
        }

class ClinicalNote(db.Model):
    __tablename__ = 'clinical_notes'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)
    subjective = db.Column(db.Text, nullable=True) # Patient chief complaint & history
    objective = db.Column(db.Text, nullable=True)  # Clinical findings & vitals
    assessment = db.Column(db.Text, nullable=True) # Diagnosis
    plan = db.Column(db.Text, nullable=True)       # Treatment plan & prescription
    is_ai_draft = db.Column(db.Boolean, default=False) # Voice-to-notes AI generated
    raw_transcript = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    doctor = db.relationship('Doctor')

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'doctor_name': self.doctor.name if self.doctor else 'Dr. Sharma',
            'subjective': self.subjective,
            'objective': self.objective,
            'assessment': self.assessment,
            'plan': self.plan,
            'is_ai_draft': self.is_ai_draft,
            'raw_transcript': self.raw_transcript,
            'date_formatted': self.created_at.strftime('%d %b %Y, %I:%M %p')
        }
