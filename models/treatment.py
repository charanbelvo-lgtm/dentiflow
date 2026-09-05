from datetime import datetime
from . import db

class TreatmentMaster(db.Model):
    __tablename__ = 'treatment_masters'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False) # e.g. "RCT-01", "CRW-02"
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False) # Preventive, Endodontics, Prosthodontics, Orthodontics, Periodontics, Surgery, Cosmetic
    default_cost = db.Column(db.Float, nullable=False)
    duration_minutes = db.Column(db.Integer, default=45)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'category': self.category,
            'default_cost': self.default_cost,
            'duration_minutes': self.duration_minutes,
            'description': self.description
        }

class TreatmentPlan(db.Model):
    __tablename__ = 'treatment_plans'

    id = db.Column(db.Integer, primary_key=True)
    plan_number = db.Column(db.String(30), unique=True, nullable=False) # e.g. "TP-2026-042"
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)
    title = db.Column(db.String(150), nullable=False) # e.g. "Full Mouth Rehabilitation & Anterior Aesthetics"
    status = db.Column(db.String(50), default='Proposed') # Proposed, Accepted, In Progress, Completed, Rejected
    total_cost = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    net_cost = db.Column(db.Float, default=0.0)
    accepted_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text, nullable=True)
    is_converted_to_invoice = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    doctor = db.relationship('Doctor')
    phases = db.relationship('TreatmentPlanPhase', backref='treatment_plan', cascade='all, delete-orphan', lazy=True, order_by='TreatmentPlanPhase.phase_number')

    def to_dict(self):
        return {
            'id': self.id,
            'plan_number': self.plan_number,
            'patient_id': self.patient_id,
            'patient_name': self.patient.name if self.patient else '',
            'doctor_name': self.doctor.name if self.doctor else 'Dr. Sharma',
            'title': self.title,
            'status': self.status,
            'total_cost': self.total_cost,
            'discount_amount': self.discount_amount,
            'net_cost': self.net_cost,
            'accepted_amount': self.accepted_amount,
            'pending_amount': max(0.0, self.net_cost - self.accepted_amount),
            'notes': self.notes,
            'is_converted_to_invoice': self.is_converted_to_invoice,
            'phases': [p.to_dict() for p in self.phases],
            'created_at': self.created_at.strftime('%d %b %Y')
        }

class TreatmentPlanPhase(db.Model):
    __tablename__ = 'treatment_plan_phases'

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('treatment_plans.id'), nullable=False)
    phase_number = db.Column(db.Integer, nullable=False, default=1) # Phase 1, Phase 2, etc.
    title = db.Column(db.String(100), nullable=False) # e.g. "Phase 1: Emergency & Pain Relief", "Phase 2: Restorative"
    status = db.Column(db.String(50), default='Pending') # Pending, In Progress, Completed
    estimated_duration_weeks = db.Column(db.Integer, default=2)

    items = db.relationship('TreatmentPlanItem', backref='phase', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        phase_cost = sum(item.net_cost for item in self.items)
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'phase_number': self.phase_number,
            'title': self.title,
            'status': self.status,
            'estimated_duration_weeks': self.estimated_duration_weeks,
            'phase_cost': phase_cost,
            'items': [item.to_dict() for item in self.items]
        }

class TreatmentPlanItem(db.Model):
    __tablename__ = 'treatment_plan_items'

    id = db.Column(db.Integer, primary_key=True)
    phase_id = db.Column(db.Integer, db.ForeignKey('treatment_plan_phases.id'), nullable=False)
    tooth_number = db.Column(db.String(20), nullable=True) # e.g. "16", "11, 21", "Full Arch"
    procedure_name = db.Column(db.String(100), nullable=False) # e.g. "Root Canal Treatment"
    unit_cost = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0.0)
    net_cost = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Pending') # Pending, Completed, Cancelled

    def to_dict(self):
        return {
            'id': self.id,
            'phase_id': self.phase_id,
            'tooth_number': self.tooth_number or 'General',
            'procedure_name': self.procedure_name,
            'unit_cost': self.unit_cost,
            'discount': self.discount,
            'net_cost': self.net_cost,
            'status': self.status
        }
