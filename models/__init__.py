from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User, AuditLog
from .patient import Patient, MedicalAlert, FamilyMember, PatientDocument
from .doctor import Doctor, Chair, Branch, StaffShift, LeaveRequest
from .appointment import Appointment, QueueToken, Waitlist
from .clinical import ToothFinding, PeriodontalRecord, Prescription, PrescriptionItem, XRayImage, ClinicalNote
from .treatment import TreatmentMaster, TreatmentPlan, TreatmentPlanPhase, TreatmentPlanItem
from .invoice import Invoice, InvoiceItem, Payment, EMIPlan, PaymentInstallment, InsuranceClaim
from .inventory import InventoryItem, Supplier, PurchaseOrder, InventoryLog
from .operations import LabOrder, Equipment, ReferralDoctor, FeedbackNPS, Campaign
