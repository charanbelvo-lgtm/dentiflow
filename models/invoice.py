from datetime import datetime
from . import db

class Invoice(db.Model):
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(30), unique=True, nullable=False, index=True) # e.g. "INV-2026-1029"
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    tax_rate = db.Column(db.Float, default=18.0) # GST 18% (CGST 9% + SGST 9%)
    tax_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)
    due_amount = db.Column(db.Float, default=0.0)
    
    status = db.Column(db.String(50), default='Pending') # Paid, Partial, Pending, Cancelled, Refunded
    payment_method = db.Column(db.String(50), default='UPI') # UPI, Card, Cash, Insurance, EMI
    notes = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    doctor = db.relationship('Doctor')
    branch = db.relationship('Branch')
    items = db.relationship('InvoiceItem', backref='invoice', cascade='all, delete-orphan', lazy=True)
    payments = db.relationship('Payment', backref='invoice', cascade='all, delete-orphan', lazy=True)
    emi_plan = db.relationship('EMIPlan', backref='invoice', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        cgst = self.tax_amount / 2.0 if self.tax_amount else 0.0
        sgst = self.tax_amount / 2.0 if self.tax_amount else 0.0
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'patient_id': self.patient_id,
            'patient_name': self.patient.name if self.patient else 'Unknown',
            'patient_phone': self.patient.phone if self.patient else '',
            'patient_email': self.patient.email if self.patient else '',
            'patient_address': self.patient.address if self.patient else '',
            'doctor_name': self.doctor.name if self.doctor else 'Dr. Sharma',
            'doctor_degree': self.doctor.degree if self.doctor else 'BDS, MDS',
            'doctor_reg': self.doctor.registration_no if self.doctor else 'KDC-28492-A',
            'branch_name': self.branch.name if self.branch else 'Downtown Dental',
            'branch_address': self.branch.address if self.branch else '100 Feet Rd, Indiranagar',
            'subtotal': self.subtotal,
            'discount_amount': self.discount_amount,
            'tax_rate': self.tax_rate,
            'tax_amount': self.tax_amount,
            'cgst_amount': cgst,
            'sgst_amount': sgst,
            'total_amount': self.total_amount,
            'paid_amount': self.paid_amount,
            'due_amount': self.due_amount,
            'status': self.status,
            'payment_method': self.payment_method,
            'notes': self.notes,
            'due_date': self.due_date.strftime('%d %b %Y') if self.due_date else '',
            'created_at': self.created_at.strftime('%d %b %Y, %I:%M %p'),
            'date_only': self.created_at.strftime('%d %b %Y'),
            'items': [item.to_dict() for item in self.items],
            'payments': [p.to_dict() for p in self.payments],
            'has_emi': self.emi_plan is not None
        }

class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False) # e.g. "Root Canal Treatment - Tooth #16"
    sac_code = db.Column(db.String(20), default='999312') # Dental Healthcare SAC code
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0.0)
    taxable_amount = db.Column(db.Float, nullable=False)
    gst_rate = db.Column(db.Float, default=18.0)
    total_amount = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'sac_code': self.sac_code,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'discount': self.discount,
            'taxable_amount': self.taxable_amount,
            'gst_rate': self.gst_rate,
            'total_amount': self.total_amount
        }

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(30), unique=True, nullable=False) # e.g. "RCP-2026-904"
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False) # UPI, Card, Cash, NetBanking, Insurance, EMI
    transaction_id = db.Column(db.String(100), nullable=True) # UPI Ref / Card Auth / Bank Ref
    notes = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='Success') # Success, Pending, Failed, Refunded
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient')

    def to_dict(self):
        return {
            'id': self.id,
            'receipt_number': self.receipt_number,
            'invoice_id': self.invoice_id,
            'invoice_number': self.invoice.invoice_number if self.invoice else '',
            'patient_id': self.patient_id,
            'patient_name': self.patient.name if self.patient else '',
            'amount': self.amount,
            'payment_method': self.payment_method,
            'transaction_id': self.transaction_id or 'TXN-' + str(self.id).zfill(6),
            'status': self.status,
            'payment_date': self.payment_date.strftime('%d %b %Y, %I:%M %p')
        }

class EMIPlan(db.Model):
    __tablename__ = 'emi_plans'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    tenure_months = db.Column(db.Integer, default=6) # 3, 6, 9, 12 months
    monthly_installment = db.Column(db.Float, nullable=False)
    down_payment = db.Column(db.Float, default=0.0)
    interest_rate = db.Column(db.Float, default=0.0) # 0% No Cost EMI mock
    status = db.Column(db.String(50), default='Active') # Active, Completed, Defaulted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    installments = db.relationship('PaymentInstallment', backref='emi_plan', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'total_amount': self.total_amount,
            'tenure_months': self.tenure_months,
            'monthly_installment': self.monthly_installment,
            'down_payment': self.down_payment,
            'interest_rate': self.interest_rate,
            'status': self.status,
            'installments': [inst.to_dict() for inst in self.installments]
        }

class PaymentInstallment(db.Model):
    __tablename__ = 'payment_installments'

    id = db.Column(db.Integer, primary_key=True)
    emi_plan_id = db.Column(db.Integer, db.ForeignKey('emi_plans.id'), nullable=False)
    installment_no = db.Column(db.Integer, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    paid_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default='Pending') # Pending, Paid, Overdue
    payment_method = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'installment_no': self.installment_no,
            'due_date': self.due_date.strftime('%d %b %Y'),
            'amount': self.amount,
            'paid_date': self.paid_date.strftime('%d %b %Y') if self.paid_date else None,
            'status': self.status,
            'payment_method': self.payment_method
        }

class InsuranceClaim(db.Model):
    __tablename__ = 'insurance_claims'

    id = db.Column(db.Integer, primary_key=True)
    claim_number = db.Column(db.String(30), unique=True, nullable=False) # e.g. "CLM-2026-881"
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    provider_name = db.Column(db.String(100), nullable=False) # Star Health, Care Health, HDFC ERGO, etc.
    policy_number = db.Column(db.String(50), nullable=False)
    claim_amount = db.Column(db.Float, nullable=False)
    approved_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='Submitted') # Submitted, Under Review, Approved, Rejected, Pending Documents, Paid
    tpa_name = db.Column(db.String(100), default='Medi Assist TPA')
    notes = db.Column(db.Text, nullable=True)
    submitted_date = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient')

    def to_dict(self):
        return {
            'id': self.id,
            'claim_number': self.claim_number,
            'patient_id': self.patient_id,
            'patient_name': self.patient.name if self.patient else '',
            'provider_name': self.provider_name,
            'policy_number': self.policy_number,
            'claim_amount': self.claim_amount,
            'approved_amount': self.approved_amount,
            'status': self.status,
            'tpa_name': self.tpa_name,
            'notes': self.notes,
            'submitted_date': self.submitted_date.strftime('%d %b %Y')
        }
