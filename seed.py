import os
from datetime import datetime, date, timedelta
from app import create_app
from models import (
    db, User, AuditLog, Patient, MedicalAlert, FamilyMember, PatientDocument,
    Doctor, Chair, Branch, StaffShift, LeaveRequest,
    Appointment, QueueToken, Waitlist,
    ToothFinding, PeriodontalRecord, Prescription, PrescriptionItem, XRayImage, ClinicalNote,
    TreatmentMaster, TreatmentPlan, TreatmentPlanPhase, TreatmentPlanItem,
    Invoice, InvoiceItem, Payment, EMIPlan, PaymentInstallment, InsuranceClaim,
    InventoryItem, Supplier, PurchaseOrder, InventoryLog,
    LabOrder, Equipment, ReferralDoctor, FeedbackNPS, Campaign
)

app = create_app()

def seed_database(reset=False):
    with app.app_context():
        if reset and os.environ.get('DENTIFLOW_ALLOW_DEMO_RESET') != '1':
            raise RuntimeError('Destructive demo reset requires DENTIFLOW_ALLOW_DEMO_RESET=1')
        print('[INFO] ' + ('Rebuilding and seeding' if reset else 'Checking and seeding') + ' DentiFlow database...')
        if reset:
            db.drop_all()
        db.create_all()
        if not reset and User.query.first():
            print('[INFO] Existing data found; leaving it unchanged.')
            return

        # 1. Branches
        branches_data = [
            Branch(name='Downtown Dental Flagship', code='DT-01', address='100 Feet Rd, Indiranagar, Bengaluru, KA 560038', city='Bengaluru', phone='+91 80 4123 4567', email='indiranagar@dentiflow.com', is_main=True),
            Branch(name='Koramangala Specialty Clinic', code='KM-02', address='80 Feet Rd, 4th Block, Koramangala, Bengaluru, KA 560034', city='Bengaluru', phone='+91 80 4123 4568', email='koramangala@dentiflow.com'),
            Branch(name='Whitefield TechPark Hub', code='WF-03', address='ITPB Main Rd, Whitefield, Bengaluru, KA 560066', city='Bengaluru', phone='+91 80 4123 4569', email='whitefield@dentiflow.com'),
            Branch(name='Jayanagar Family Practice', code='JN-04', address='9th Main, 4th Block, Jayanagar, Bengaluru, KA 560011', city='Bengaluru', phone='+91 80 4123 4570', email='jayanagar@dentiflow.com')
        ]
        db.session.add_all(branches_data)
        db.session.commit()

        # 2. Chairs for Main Branch
        chairs_data = [
            Chair(branch_id=1, chair_number='Chair 01', name='Operatory Alpha (Endodontics)', status='In Treatment', current_patient='Aravind', current_doctor='Dr. Ananya Sharma', current_procedure='Root Canal Treatment', session_start_time=datetime.utcnow() - timedelta(minutes=32), equipment_specs='Anthos A3 Plus + Sirona RVG'),
            Chair(branch_id=1, chair_number='Chair 02', name='Operatory Beta (Oral Surgery)', status='Available', current_patient=None, current_doctor=None, current_procedure=None, equipment_specs='Kavo Primus 1058 Life + Apex Locator'),
            Chair(branch_id=1, chair_number='Chair 03', name='Operatory Gamma (Orthodontics)', status='Cleaning', current_patient=None, current_doctor='Dr. Rohan Patel', current_procedure='Aligner Fitting Completed', equipment_specs='A-dec 500 LED Operatory'),
            Chair(branch_id=1, chair_number='Chair 04', name='Operatory Delta (Preventive & Hygiene)', status='Patient Waiting', current_patient='Lokesh', current_doctor='Dr. Meera Nair', current_procedure='Scaling & Polishing', equipment_specs='Belmont Clesta II Dental Chair')
        ]
        db.session.add_all(chairs_data)
        db.session.commit()

        # 3. Users
        users = [
            User(email='admin@dentiflow.com', name='Dr. Rajesh Verma', role='admin', phone='+91 98765 43210', branch_id=1, avatar='/static/img/cartoon-doctor.svg'),
            User(email='doctor@dentiflow.com', name='Dr. Ananya Sharma', role='doctor', phone='+91 98765 43211', branch_id=1, avatar='/static/img/cartoon-doctor.svg'),
            User(email='reception@dentiflow.com', name='Pooja Hegde', role='receptionist', phone='+91 98765 43212', branch_id=1, avatar='/static/img/cartoon-patient.svg'),
            User(email='budigeashwinigoud@gmail.com', name='Ashwini Goud', role='patient', phone='+91 98765 43213', branch_id=1, avatar='/static/img/cartoon-patient.svg')
        ]
        for u in users:
            u.set_password('patient123' if u.role == 'patient' else u.email.split('@')[0] + '123')
        db.session.add_all(users)
        db.session.commit()

        # 4. Doctors
        doctors = [
            Doctor(user_id=2, branch_id=1, name='Dr. Ananya Sharma', specialty='Chief Endodontist & Cosmetic Dentist', degree='BDS, MDS (Endodontics)', registration_no='KDC-28492-A', phone='+91 98765 43211', email='ananya.sharma@dentiflow.com', avatar='/static/img/cartoon-doctor.svg', assigned_chair='Chair 01', experience_years=11, consultation_fee=700.0, commission_rate=35.0, rating=4.95, color_badge='#2563EB'),
            Doctor(user_id=None, branch_id=1, name='Dr. Rohan Patel', specialty='Consultant Orthodontist (Invisalign Platinum)', degree='BDS, MDS (Orthodontics), M.Orth RCSEd', registration_no='KDC-31908-B', phone='+91 98450 67890', email='rohan.patel@dentiflow.com', avatar='/static/img/cartoon-doctor.svg', assigned_chair='Chair 03', experience_years=9, consultation_fee=800.0, commission_rate=30.0, rating=4.9, color_badge='#06B6D4'),
            Doctor(user_id=None, branch_id=1, name='Dr. Meera Nair', specialty='Periodontist & Implantologist', degree='BDS, MDS (Periodontics), ICOI Fellow', registration_no='KDC-25114-C', phone='+91 98860 12345', email='meera.nair@dentiflow.com', avatar='/static/img/cartoon-doctor.svg', assigned_chair='Chair 02', experience_years=14, consultation_fee=650.0, commission_rate=30.0, rating=4.88, color_badge='#14B8A6'),
            Doctor(user_id=None, branch_id=1, name='Dr. Vikram Rao', specialty='Oral & Maxillofacial Surgeon', degree='BDS, MDS (Oral Surgery), FIBOMS', registration_no='KDC-19876-D', phone='+91 97410 99887', email='vikram.rao@dentiflow.com', avatar='/static/img/cartoon-doctor.svg', assigned_chair='Chair 04', experience_years=16, consultation_fee=900.0, commission_rate=40.0, rating=4.92, color_badge='#8B5CF6')
        ]
        db.session.add_all(doctors)
        db.session.commit()

        # 5. Treatment Master Catalog
        treatments = [
            TreatmentMaster(code='CON-01', name='Comprehensive Dental Consultation', category='Preventive', default_cost=500.0, duration_minutes=30, description='Full mouth visual examination, digital charting, and intraoral scan.'),
            TreatmentMaster(code='SCL-01', name='Ultrasonic Scaling & Airflow Polishing', category='Preventive', default_cost=1800.0, duration_minutes=40, description='Full mouth supragingival and subgingival calculus removal.'),
            TreatmentMaster(code='RCT-01', name='Rotary Single-Visit Root Canal (Anterior)', category='Endodontics', default_cost=5500.0, duration_minutes=60, description='Biomechanical preparation with rotary NiTi files and thermo-plasticized obturation.'),
            TreatmentMaster(code='RCT-02', name='Rotary Single-Visit Root Canal (Molar)', category='Endodontics', default_cost=7500.0, duration_minutes=75, description='Molar canal location with dental loupes, apex locator, and bioceramic sealer.'),
            TreatmentMaster(code='CRW-01', name='Monolithic 3D Zirconia Crown (10 Yr Warranty)', category='Prosthodontics', default_cost=8500.0, duration_minutes=45, description='CAD/CAM precision-milled multi-layer translucent zirconia crown.'),
            TreatmentMaster(code='CRW-02', name='E-Max Lithium Disilicate Ceramic Veneer/Crown', category='Cosmetic', default_cost=11000.0, duration_minutes=60, description='Ultra-aesthetic monolithic glass ceramic veneer or crown.'),
            TreatmentMaster(code='IMP-01', name='Titanium Dental Implant (Nobel Biocare / Straumann)', category='Surgery', default_cost=35000.0, duration_minutes=90, description='Surgically placed titanium implant body + custom healing abutment.'),
            TreatmentMaster(code='EXT-01', name='Impacted Third Molar Surgical Extraction', category='Surgery', default_cost=4500.0, duration_minutes=45, description='Surgical removal of horizontal/mesioangular impacted wisdom tooth with flap.'),
            TreatmentMaster(code='FIL-01', name='Tooth Colored Nano-Composite Filling (Single Surface)', category='Preventive', default_cost=1500.0, duration_minutes=30, description='3M Filtek bulk-fill restorative resin with laser light curing.'),
            TreatmentMaster(code='FIL-02', name='Tooth Colored Composite Restoration (Multi-Surface)', category='Preventive', default_cost=2500.0, duration_minutes=45, description='Layered composite aesthetic filling involving occlusal and proximal walls.'),
            TreatmentMaster(code='WHT-01', name='In-Office Laser Teeth Whitening (Zoom 4)', category='Cosmetic', default_cost=12000.0, duration_minutes=60, description='Phillips Zoom LED activation for 6-8 shades lighter teeth in single session.'),
            TreatmentMaster(code='ALN-01', name='Clear Aligners Comprehensive Plan (Both Arches)', category='Orthodontics', default_cost=85000.0, duration_minutes=45, description='Custom 3D planned sequential transparent aligners with monthly monitoring.')
        ]
        db.session.add_all(treatments)
        db.session.commit()

        # 6. Patients
        patients_data = [
            Patient(patient_id='DF-2026-001', name='Ashwini Goud', age=29, gender='Female', phone='+91 98765 43213', email='budigeashwinigoud@gmail.com', blood_group='O+', address='Indiranagar, Bengaluru', emergency_contact_name='Kavya (Sister)', emergency_contact_phone='123456780', primary_doctor_id=1, branch_id=1, abdm_health_id='ashwini.demo', outstanding_balance=2500.0, total_spent=18500.0, last_visit=datetime.utcnow() - timedelta(days=12)),
            Patient(patient_id='DF-2026-002', name='Vishal', age=35, gender='Male', phone='123456788', email='vishal@gmail.com', blood_group='B+', address='Koramangala, Bengaluru', emergency_contact_name='Meera (Spouse)', emergency_contact_phone='123456781', primary_doctor_id=2, branch_id=1, outstanding_balance=0.0, total_spent=42000.0, last_visit=datetime.utcnow() - timedelta(days=5)),
            Patient(patient_id='DF-2026-003', name='Medha', age=27, gender='Female', phone='123456787', email='medha@gmail.com', blood_group='A+', address='Whitefield, Bengaluru', emergency_contact_name='Ravi (Father)', emergency_contact_phone='123456782', primary_doctor_id=2, branch_id=1, outstanding_balance=0.0, total_spent=14500.0, last_visit=datetime.utcnow() - timedelta(days=20)),
            Patient(patient_id='DF-2026-004', name='Lokesh', age=42, gender='Male', phone='123456786', email='lokesh@gmail.com', blood_group='AB+', address='HSR Layout, Bengaluru', emergency_contact_name='Anita (Spouse)', emergency_contact_phone='123456783', primary_doctor_id=3, branch_id=1, outstanding_balance=4500.0, total_spent=31000.0, last_visit=datetime.utcnow() - timedelta(days=3)),
            Patient(patient_id='DF-2026-005', name='Aravind Kumar', age=56, gender='Male', phone='123456785', email='aravind.kumar@gmail.com', blood_group='O-', address='Malleshwaram, Bengaluru', emergency_contact_name='Anita (Spouse)', emergency_contact_phone='123456784', primary_doctor_id=4, branch_id=1, outstanding_balance=12000.0, total_spent=95000.0, last_visit=datetime.utcnow() - timedelta(days=2)),
            Patient(patient_id='DF-2026-006', name='Vishal Rao', age=24, gender='Male', phone='123456784', email='vishal.rao@gmail.com', blood_group='A-', address='Bellandur, Bengaluru', emergency_contact_name='Sunita (Mother)', emergency_contact_phone='123456783', primary_doctor_id=1, branch_id=1, outstanding_balance=0.0, total_spent=16000.0, last_visit=datetime.utcnow() - timedelta(days=15)),
            Patient(patient_id='DF-2026-007', name='Medha Nair', age=62, gender='Female', phone='123456783', email='medha.nair@gmail.com', blood_group='B+', address='Jayanagar, Bengaluru', emergency_contact_name='Deepak (Brother)', emergency_contact_phone='123456782', primary_doctor_id=3, branch_id=1, outstanding_balance=8500.0, total_spent=64000.0, last_visit=datetime.utcnow() - timedelta(days=1)),
            Patient(patient_id='DF-2026-008', name='Lokesh Iyer', age=31, gender='Male', phone='123456782', email='lokesh.iyer@gmail.com', blood_group='O+', address='Electronic City, Bengaluru', emergency_contact_name='Ganesh (Brother)', emergency_contact_phone='123456781', primary_doctor_id=1, branch_id=1, outstanding_balance=0.0, total_spent=28500.0, last_visit=datetime.utcnow() - timedelta(days=8))
        ]
        db.session.add_all(patients_data)
        db.session.commit()

        # 7. Medical Alerts
        alerts = [
            MedicalAlert(patient_id=1, alert_type='Allergy', alert_text='⚠ ALLERGY: Penicillin & Amoxicillin (Severe Anaphylaxis)', is_critical=True),
            MedicalAlert(patient_id=4, alert_type='Condition', alert_text='Hypertension (On Amlodipine 5mg OD)', is_critical=False),
            MedicalAlert(patient_id=5, alert_type='Condition', alert_text='Diabetic (Type 2 - Fasting Blood Sugar 135 mg/dL)', is_critical=True),
            MedicalAlert(patient_id=5, alert_type='Medication', alert_text='⚠ Blood Thinner: Ecosprin 75mg (Consult Cardiologist before surgery)', is_critical=True),
            MedicalAlert(patient_id=7, alert_type='Condition', alert_text='Cardiac Pacemaker fitted (No Electrosurgery / Ultrasonic Scaler with Caution)', is_critical=True)
        ]
        db.session.add_all(alerts)

        # 8. Family Members
        family = [
            FamilyMember(patient_id=1, name='Priya Mehta', relation='Spouse', phone='+91 98451 22335', age=32),
            FamilyMember(patient_id=1, name='Aarav Mehta', relation='Child', phone='+91 98451 22334', age=7),
            FamilyMember(patient_id=2, name='Ramesh Sharma', relation='Parent', phone='+91 97412 33440', age=58)
        ]
        db.session.add_all(family)

        # 9. Patient Documents
        docs = [
            PatientDocument(patient_id=1, title='Informed Consent Form - Endodontic Therapy', doc_type='Consent Form', file_url='/static/images/consent_form_signed.pdf', file_size='840 KB'),
            PatientDocument(patient_id=1, title='Digital Intraoral Full Scan (STL)', doc_type='Medical Report', file_url='/static/images/intraoral_scan.stl', file_size='18.4 MB'),
            PatientDocument(patient_id=5, title='Pre-Surgical Cardiac Clearance Letter', doc_type='Medical Report', file_url='/static/images/cardiac_clearance.pdf', file_size='1.1 MB')
        ]
        db.session.add_all(docs)
        db.session.commit()

        # 10. Today's Appointments & Queue
        today = date.today()
        appointments_today = [
            Appointment(appointment_number='APT-1081', patient_id=1, doctor_id=1, chair_id=1, branch_id=1, appointment_date=today, start_time='09:00 AM', duration_minutes=45, procedure_name='Root Canal Treatment (Tooth #16)', status='In Treatment', booking_source='Walk-in', deposit_amount=1000.0, notes='Second sitting for obturation. Check for percussion tenderness.', is_emergency=False),
            Appointment(appointment_number='APT-1082', patient_id=2, doctor_id=2, chair_id=3, branch_id=1, appointment_date=today, start_time='09:30 AM', duration_minutes=30, procedure_name='Clear Aligner Progress Review (Tray #14)', status='Completed', booking_source='Instagram', deposit_amount=0.0, notes='Delivered Aligner Set #14 to #18. Tracking is optimal.', is_emergency=False),
            Appointment(appointment_number='APT-1083', patient_id=3, doctor_id=2, chair_id=3, branch_id=1, appointment_date=today, start_time='10:15 AM', duration_minutes=30, procedure_name='Pediatric Space Maintainer & Fluoride', status='Waiting', booking_source='Google', deposit_amount=500.0, notes='Patient is cooperative with parental presence.', is_emergency=False),
            Appointment(appointment_number='APT-1084', patient_id=4, doctor_id=3, chair_id=4, branch_id=1, appointment_date=today, start_time='11:00 AM', duration_minutes=40, procedure_name='Ultrasonic Scaling & Periodontal Flap Consult', status='Waiting', booking_source='Referral', deposit_amount=0.0, notes='Bleeding gums on brushing. Deep pockets quadrant 1.', is_emergency=False),
            Appointment(appointment_number='APT-1085', patient_id=5, doctor_id=4, chair_id=2, branch_id=1, appointment_date=today, start_time='11:45 AM', duration_minutes=60, procedure_name='Emergency Severe Toothache - Extraction/RCT', status='Confirmed', booking_source='Walk-in', deposit_amount=1500.0, notes='Severe throbbing pain in lower left molar radiating to ear.', is_emergency=True),
            Appointment(appointment_number='APT-1086', patient_id=6, doctor_id=1, chair_id=1, branch_id=1, appointment_date=today, start_time='02:00 PM', duration_minutes=45, procedure_name='Laser Teeth Whitening (Zoom 4)', status='Confirmed', booking_source='Instagram', deposit_amount=2000.0, notes='Bride-to-be cosmetic enhancement package.', is_emergency=False),
            Appointment(appointment_number='APT-1087', patient_id=7, doctor_id=3, chair_id=2, branch_id=1, appointment_date=today, start_time='03:30 PM', duration_minutes=45, procedure_name='Dental Implant Stage 2 Uncovery', status='Confirmed', booking_source='Referral', deposit_amount=5000.0, notes='Healing abutment placement for Tooth #36 implant.', is_emergency=False),
            Appointment(appointment_number='APT-1088', patient_id=8, doctor_id=1, chair_id=1, branch_id=1, appointment_date=today, start_time='04:30 PM', duration_minutes=30, procedure_name='Composite Restorations (Teeth #11, #21)', status='Confirmed', booking_source='WhatsApp', deposit_amount=500.0, notes='Incisal angle chip repair with aesthetic resin.', is_emergency=False),
            # Upcoming days
            Appointment(appointment_number='APT-1089', patient_id=1, doctor_id=1, chair_id=1, branch_id=1, appointment_date=today + timedelta(days=2), start_time='10:00 AM', duration_minutes=45, procedure_name='Zirconia Crown Measurement & Scan', status='Confirmed', booking_source='Walk-in', deposit_amount=0.0, notes='Post-RCT crown preparation.', is_emergency=False),
            Appointment(appointment_number='APT-1090', patient_id=2, doctor_id=2, chair_id=3, branch_id=1, appointment_date=today + timedelta(days=3), start_time='11:30 AM', duration_minutes=30, procedure_name='Aligner IPR & Attachment Check', status='Confirmed', booking_source='Instagram', deposit_amount=0.0, notes='IPR 0.2mm lower incisors.', is_emergency=False)
        ]
        db.session.add_all(appointments_today)
        db.session.commit()

        # 11. Live Queue Tokens for Today
        tokens = [
            QueueToken(appointment_id=1, patient_id=1, token_number='Token #014', doctor_id=1, chair_id=1, procedure_name='Root Canal Treatment', status='Serving', is_emergency=False, estimated_wait_min=0, called_at=datetime.utcnow() - timedelta(minutes=30)),
            QueueToken(appointment_id=3, patient_id=3, token_number='Token #015', doctor_id=2, chair_id=3, procedure_name='Pediatric Fluoride & Maintainer', status='Waiting', is_emergency=False, estimated_wait_min=10),
            QueueToken(appointment_id=4, patient_id=4, token_number='Token #016', doctor_id=3, chair_id=4, procedure_name='Scaling & Periodontal Exam', status='Waiting', is_emergency=False, estimated_wait_min=20),
            QueueToken(appointment_id=5, patient_id=5, token_number='Token #017', doctor_id=4, chair_id=2, procedure_name='Emergency Toothache Pain Relief', status='Waiting', is_emergency=True, estimated_wait_min=5)
        ]
        db.session.add_all(tokens)
        db.session.commit()

        # 12. Tooth Findings for Rahul Mehta (Patient #1) and others
        # Dental Notation (FDI 11-48)
        findings_data = [
            ToothFinding(patient_id=1, tooth_number=16, status='Root Canal', surfaces='MOD', diagnosis='Deep carious lesion involving pulp with periapical lucency', recommended_treatment='Rotary RCT + CAD/CAM Zirconia Crown', estimated_cost=15500.0, doctor_id=1),
            ToothFinding(patient_id=1, tooth_number=17, status='Cavity', surfaces='O', diagnosis='Enamel-dentin caries on occlusal fissure', recommended_treatment='Composite Nano-Hybrid Filling', estimated_cost=2500.0, doctor_id=1),
            ToothFinding(patient_id=1, tooth_number=26, status='Filling', surfaces='MO', diagnosis='Existing amalgam restoration with marginal breakdown', recommended_treatment='Replacement with Aesthetic Ceramic Inlay', estimated_cost=4500.0, doctor_id=1),
            ToothFinding(patient_id=1, tooth_number=36, status='Crown', surfaces='Full', diagnosis='Previous PFM crown intact with minor gingival margin discrepancy', recommended_treatment='Routine Periodic Monitoring', estimated_cost=0.0, doctor_id=1),
            ToothFinding(patient_id=1, tooth_number=48, status='Extraction', surfaces='Full', diagnosis='Horizontally impacted third molar causing food lodgement', recommended_treatment='Surgical Disimpaction', estimated_cost=4500.0, doctor_id=4),
            ToothFinding(patient_id=1, tooth_number=11, status='Watch', surfaces='I', diagnosis='Incisal attrition and micro-craze lines', recommended_treatment='Nightguard for bruxism + Remineralizing gel', estimated_cost=3500.0, doctor_id=1),
            ToothFinding(patient_id=1, tooth_number=21, status='Watch', surfaces='I', diagnosis='Incisal enamel wear facets', recommended_treatment='Monitoring', estimated_cost=0.0, doctor_id=1),
            ToothFinding(patient_id=1, tooth_number=46, status='Healthy', surfaces='', diagnosis='Healthy intact tooth', recommended_treatment='None', estimated_cost=0.0, doctor_id=1)
        ]
        db.session.add_all(findings_data)

        # 13. Periodontal Charting Records
        perio_records = [
            PeriodontalRecord(patient_id=1, tooth_number=16, pocket_depth_mb=5, pocket_depth_b=4, pocket_depth_db=5, pocket_depth_ml=4, pocket_depth_l=3, pocket_depth_dl=4, bleeding_on_probing=True, mobility='I', gingival_margin=1),
            PeriodontalRecord(patient_id=1, tooth_number=17, pocket_depth_mb=3, pocket_depth_b=2, pocket_depth_db=3, pocket_depth_ml=3, pocket_depth_l=2, pocket_depth_dl=3, bleeding_on_probing=False, mobility='0', gingival_margin=0),
            PeriodontalRecord(patient_id=1, tooth_number=26, pocket_depth_mb=4, pocket_depth_b=3, pocket_depth_db=4, pocket_depth_ml=4, pocket_depth_l=3, pocket_depth_dl=4, bleeding_on_probing=True, mobility='0', gingival_margin=0),
            PeriodontalRecord(patient_id=1, tooth_number=36, pocket_depth_mb=3, pocket_depth_b=2, pocket_depth_db=3, pocket_depth_ml=2, pocket_depth_l=2, pocket_depth_dl=2, bleeding_on_probing=False, mobility='0', gingival_margin=0),
            PeriodontalRecord(patient_id=1, tooth_number=46, pocket_depth_mb=2, pocket_depth_b=2, pocket_depth_db=2, pocket_depth_ml=2, pocket_depth_l=2, pocket_depth_dl=2, bleeding_on_probing=False, mobility='0', gingival_margin=0)
        ]
        db.session.add_all(perio_records)

        # 14. X-Rays / Imaging with AI Anomaly Detection
        xrays_data = [
            XRayImage(patient_id=1, title='Full Mouth Digital Panoramic OPG', xray_type='OPG', image_url='https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?auto=format&fit=crop&q=80&w=800', comparison_image_url='https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?auto=format&fit=crop&q=80&w=800', ai_cavity_detected=True, ai_bone_loss_detected=True, ai_periapical_lesion=True, ai_confidence=96.4, ai_analysis_notes='AI Indication: Deep radiolucency on distal coronal aspect of Tooth #16 communicating with coronal pulp chamber. Circumscribed periapical radiolucency ~3.2mm on mesiobuccal root apex. Horizontal bone crest reduction ~1.8mm in Quadrant 1.', captured_date=datetime.utcnow() - timedelta(days=12)),
            XRayImage(patient_id=1, title='Intraoral Periapical (IOPA) - Upper Right Molar #16', xray_type='RVG', image_url='https://images.unsplash.com/photo-1516549655169-df83a0774514?auto=format&fit=crop&q=80&w=800', ai_cavity_detected=True, ai_periapical_lesion=True, ai_confidence=98.1, ai_analysis_notes='AI Indication: Well-defined canal anatomy (MB1, MB2, DB, Palatal). Working length estimation approx 21.5mm. Periapical rarefaction noted.', captured_date=datetime.utcnow() - timedelta(days=2)),
            XRayImage(patient_id=1, title='Before vs After Smile Aesthetics (Anterior Restoration)', xray_type='Before/After', image_url='https://images.unsplash.com/photo-1606811841689-23dfddce3e95?auto=format&fit=crop&q=80&w=800', comparison_image_url='https://images.unsplash.com/photo-1606811841689-23dfddce3e95?auto=format&fit=crop&q=80&w=800', ai_confidence=99.0, ai_analysis_notes='Post-operative aesthetic alignment and optical shade match delta E < 1.2.')
        ]
        db.session.add_all(xrays_data)

        # 15. Clinical Notes (including AI Voice-to-notes SOAP notes)
        notes = [
            ClinicalNote(patient_id=1, doctor_id=1, subjective='Patient Rahul Mehta presents with dull lingering throbbing ache in right upper back tooth aggravated on hot foods and mastication for 4 days.', objective='Clinical exam shows deep caries on #16 disto-occlusal surface. TTP positive (+). Cold test: prolonged lingering response (>15s). IOPA confirms pulp involvement with MB periapical widening.', assessment='Symptomatic Irreversible Pulpitis with Symptomatic Apical Periodontitis in Tooth #16.', plan='1. Single/Two-visit Rotary Endodontic Therapy #16 under rubber dam.\n2. Occlusal reduction and analgesic coverage.\n3. Post-endodontic CAD/CAM Monolithic Zirconia Crown.', is_ai_draft=False, raw_transcript=None),
            ClinicalNote(patient_id=1, doctor_id=1, subjective='Patient attended second appointment for root canal obturation. Pain completely resolved. No swelling or percussion sensitivity.', objective='Canals dry, no foul exudate. Master cone fit verified radiographically.', assessment='Asymptomatic Tooth #16 ready for 3D obturation.', plan='Obturated with AH Plus Bioceramic sealer and gutta percha. Coronal seal with composite. Proceeded with crown preparation impression.', is_ai_draft=True, raw_transcript="Patient arrived for second visit. Reports pain has subsided completely. Loupe inspection shows canals clean and dry. Master cone fit confirmed. 3D warm vertical condensation performed. Patient tolerated well.")
        ]
        db.session.add_all(notes)

        # 16. Digital Prescriptions
        rx = Prescription(rx_number='RX-2026-089', patient_id=1, doctor_id=1, diagnosis='Acute Periapical Abscess / Post-RCT Pain Management', general_advice='Take medications strictly after food. Rinse mouth with warm saline water 3 times a day. Avoid chewing hard food on upper right side until crown is cemented.')
        db.session.add(rx)
        db.session.commit()

        rx_items = [
            PrescriptionItem(prescription_id=rx.id, medicine_name='Augmentin 625mg (Amoxicillin + Clavulanic Acid)', dosage='1 Tablet', frequency='Twice daily (1-0-1)', duration='5 days', instructions='After meals with full glass of water'),
            PrescriptionItem(prescription_id=rx.id, medicine_name='Combiflam (Ibuprofen 400mg + Paracetamol 325mg)', dosage='1 Tablet', frequency='Thrice daily (1-1-1)', duration='3 days', instructions='Strictly after food (SOS for pain)'),
            PrescriptionItem(prescription_id=rx.id, medicine_name='Pan-D (Pantoprazole 40mg + Domperidone 30mg)', dosage='1 Capsule', frequency='Once daily (1-0-0)', duration='5 days', instructions='Empty stomach in morning'),
            PrescriptionItem(prescription_id=rx.id, medicine_name='Hexidine 0.2% Chlorhexidine Mouthwash', dosage='10 ml', frequency='Twice daily', duration='7 days', instructions='Swish for 60 seconds after brushing, do not eat for 30 min')
        ]
        db.session.add_all(rx_items)

        # 17. Treatment Plans
        tp1 = TreatmentPlan(plan_number='TP-2026-042', patient_id=1, doctor_id=1, title='Comprehensive Endodontic & Aesthetic Restorative Plan', status='In Progress', total_cost=26500.0, discount_amount=1500.0, net_cost=25000.0, accepted_amount=17500.0, notes='Phase 1 paid and ongoing. Patient opted for 3D Zirconia Crown over PFM.')
        db.session.add(tp1)
        db.session.commit()

        phase1 = TreatmentPlanPhase(plan_id=tp1.id, phase_number=1, title='Phase 1: Pain Relief & Endodontic Stabilization', status='In Progress', estimated_duration_weeks=1)
        phase2 = TreatmentPlanPhase(plan_id=tp1.id, phase_number=2, title='Phase 2: Permanent Prosthodontic Rehabilitation', status='Pending', estimated_duration_weeks=2)
        phase3 = TreatmentPlanPhase(plan_id=tp1.id, phase_number=3, title='Phase 3: Preventive Hygiene & Nightguard Maintenance', status='Pending', estimated_duration_weeks=1)
        db.session.add_all([phase1, phase2, phase3])
        db.session.commit()

        p_items = [
            TreatmentPlanItem(phase_id=phase1.id, tooth_number='16', procedure_name='Rotary Molar Root Canal Therapy', unit_cost=7500.0, discount=500.0, net_cost=7000.0, status='Completed'),
            TreatmentPlanItem(phase_id=phase1.id, tooth_number='16', procedure_name='Core Build-up & Fiber Post', unit_cost=2500.0, discount=0.0, net_cost=2500.0, status='In Progress'),
            TreatmentPlanItem(phase_id=phase2.id, tooth_number='16', procedure_name='Monolithic 3D Zirconia Crown (10 Yr Warranty)', unit_cost=8500.0, discount=500.0, net_cost=8000.0, status='Pending'),
            TreatmentPlanItem(phase_id=phase2.id, tooth_number='17', procedure_name='Composite Nano-Hybrid Restoration', unit_cost=2500.0, discount=0.0, net_cost=2500.0, status='Pending'),
            TreatmentPlanItem(phase_id=phase3.id, tooth_number='Full Arch', procedure_name='Ultrasonic Scaling & Airflow Polishing', unit_cost=1800.0, discount=300.0, net_cost=1500.0, status='Pending'),
            TreatmentPlanItem(phase_id=phase3.id, tooth_number='Upper Arch', procedure_name='Custom Hard-Soft Occlusal Nightguard', unit_cost=3700.0, discount=200.0, net_cost=3500.0, status='Pending')
        ]
        db.session.add_all(p_items)
        db.session.commit()

        # 18. Invoices, Payments, GST & EMI
        inv1 = Invoice(invoice_number='INV-2026-1029', patient_id=1, doctor_id=1, branch_id=1, subtotal=15500.0, discount_amount=1000.0, tax_rate=18.0, tax_amount=2610.0, total_amount=17110.0, paid_amount=14610.0, due_amount=2500.0, status='Partial', payment_method='UPI', notes='Advance received for RCT + Crown. Balance due on crown delivery.', due_date=today + timedelta(days=10))
        db.session.add(inv1)
        db.session.commit()

        inv_items1 = [
            InvoiceItem(invoice_id=inv1.id, description='Rotary Single-Visit Root Canal (Tooth #16)', sac_code='999312', quantity=1, unit_price=7500.0, discount=500.0, taxable_amount=7000.0, gst_rate=18.0, total_amount=8260.0),
            InvoiceItem(invoice_id=inv1.id, description='Monolithic 3D Multilayer Zirconia Crown', sac_code='999312', quantity=1, unit_price=8000.0, discount=500.0, taxable_amount=7500.0, gst_rate=18.0, total_amount=8850.0)
        ]
        db.session.add_all(inv_items1)

        pay1 = Payment(receipt_number='RCP-2026-904', invoice_id=inv1.id, patient_id=1, amount=14610.0, payment_method='UPI', transaction_id='UPI-948102948201', notes='Paid via Google Pay / QR scanner', status='Success', payment_date=datetime.utcnow() - timedelta(days=2))
        db.session.add(pay1)

        # Invoice 2 for Priya Sharma (Clear Aligners with EMI)
        inv2 = Invoice(invoice_number='INV-2026-1030', patient_id=2, doctor_id=2, branch_id=1, subtotal=60000.0, discount_amount=0.0, tax_rate=18.0, tax_amount=10800.0, total_amount=70800.0, paid_amount=23600.0, due_amount=47200.0, status='Partial', payment_method='EMI', notes='6-Month No Cost EMI Plan activated.', due_date=today + timedelta(days=30))
        db.session.add(inv2)
        db.session.commit()

        inv_items2 = [
            InvoiceItem(invoice_id=inv2.id, description='Clear Aligners Comprehensive Plan (Both Arches)', sac_code='999312', quantity=1, unit_price=60000.0, discount=0.0, taxable_amount=60000.0, gst_rate=18.0, total_amount=70800.0)
        ]
        db.session.add_all(inv_items2)

        pay2 = Payment(receipt_number='RCP-2026-905', invoice_id=inv2.id, patient_id=2, amount=23600.0, payment_method='Card', transaction_id='HDFC-POS-88912', notes='Downpayment + 1st Installment paid on HDFC Credit Card', status='Success', payment_date=datetime.utcnow() - timedelta(days=5))
        db.session.add(pay2)

        # EMI Plan for Priya
        emi = EMIPlan(invoice_id=inv2.id, patient_id=2, total_amount=70800.0, tenure_months=6, monthly_installment=11800.0, down_payment=11800.0, interest_rate=0.0, status='Active')
        db.session.add(emi)
        db.session.commit()

        installments = [
            PaymentInstallment(emi_plan_id=emi.id, installment_no=1, due_date=today - timedelta(days=5), amount=11800.0, paid_date=datetime.utcnow() - timedelta(days=5), status='Paid', payment_method='Card'),
            PaymentInstallment(emi_plan_id=emi.id, installment_no=2, due_date=today + timedelta(days=25), amount=11800.0, status='Pending'),
            PaymentInstallment(emi_plan_id=emi.id, installment_no=3, due_date=today + timedelta(days=55), amount=11800.0, status='Pending'),
            PaymentInstallment(emi_plan_id=emi.id, installment_no=4, due_date=today + timedelta(days=85), amount=11800.0, status='Pending'),
            PaymentInstallment(emi_plan_id=emi.id, installment_no=5, due_date=today + timedelta(days=115), amount=11800.0, status='Pending'),
            PaymentInstallment(emi_plan_id=emi.id, installment_no=6, due_date=today + timedelta(days=145), amount=11800.0, status='Pending')
        ]
        db.session.add_all(installments)

        # 19. Suppliers & Inventory Items
        sup1 = Supplier(name='DentSupply Prime India', contact_person='Rajesh Goyal', phone='+91 98450 11998', email='orders@dentsupply.in', address='Peenya Industrial Area, Bengaluru', rating=4.9)
        sup2 = Supplier(name='3M Oral Care Solutions', contact_person='Anita Desai', phone='+91 98110 55443', email='dentalcare@mmm.com', address='UB City, Vittal Mallya Rd, Bengaluru', rating=4.95)
        sup3 = Supplier(name='Dentsply Sirona Medical', contact_person='Karthik Reddy', phone='+91 99000 33221', email='support.india@dentsplysirona.com', address='Whitefield Techzone, Bengaluru', rating=4.85)
        db.session.add_all([sup1, sup2, sup3])
        db.session.commit()

        inventory_items = [
            InventoryItem(item_code='MAT-RES-01', name='3M Filtek Z350 XT Composite Resin (Shade A2)', category='Dental Materials', current_stock=6, min_stock_level=15, unit='syringes', unit_price=2200.0, supplier_id=2, supplier_name='3M Oral Care Solutions', batch_number='FLT-2026-99', expiry_date=today + timedelta(days=400)),
            InventoryItem(item_code='CON-GLV-01', name='Nitrile Examination Gloves (Medium / Powder-Free)', category='Consumables', current_stock=480, min_stock_level=100, unit='boxes', unit_price=420.0, supplier_id=1, supplier_name='DentSupply Prime India', batch_number='GLV-2026-12', expiry_date=today + timedelta(days=700)),
            InventoryItem(item_code='MAT-BUR-01', name='Mani Diamond Dental Burs (Assorted FG High Speed)', category='Dental Materials', current_stock=8, min_stock_level=20, unit='packs', unit_price=950.0, supplier_id=1, supplier_name='DentSupply Prime India', batch_number='BUR-2026-08', expiry_date=today + timedelta(days=900)),
            InventoryItem(item_code='MED-LID-01', name='Lignox 2% Lignocaine with Adrenaline (1:80000)', category='Medicines', current_stock=18, min_stock_level=10, unit='vials', unit_price=350.0, supplier_id=1, supplier_name='DentSupply Prime India', batch_number='LIG-2026-44', expiry_date=today + timedelta(days=320)),
            InventoryItem(item_code='LAB-ALN-01', name='Clear Aligner Thermoplastic Sheets (1.0mm Zendura)', category='Lab Materials', current_stock=25, min_stock_level=30, unit='packs', unit_price=3200.0, supplier_id=3, supplier_name='Dentsply Sirona Medical', batch_number='ZEN-2026-02', expiry_date=today + timedelta(days=600)),
            InventoryItem(item_code='CON-DAM-01', name='Sanctuary Dental Dam Kit (Latex-Free Mint)', category='Consumables', current_stock=4, min_stock_level=10, unit='kits', unit_price=1650.0, supplier_id=1, supplier_name='DentSupply Prime India', batch_number='DAM-2026-19', expiry_date=today + timedelta(days=500)),
            InventoryItem(item_code='MAT-BIO-01', name='BioRoot RCS Bioceramic Root Canal Sealer', category='Dental Materials', current_stock=12, min_stock_level=5, unit='syringes', unit_price=4800.0, supplier_id=3, supplier_name='Dentsply Sirona Medical', batch_number='BIO-2026-88', expiry_date=today + timedelta(days=450))
        ]
        db.session.add_all(inventory_items)
        db.session.commit()

        # Purchase Orders
        po = PurchaseOrder(po_number='PO-2026-033', supplier_name='3M Oral Care Solutions', total_amount=38500.0, status='Ordered', items_summary='15x 3M Filtek Composite A2, 5x Single Bond Universal Adhesive, 10x Sof-Lex Polishing Discs', order_date=datetime.utcnow() - timedelta(days=1), expected_delivery=today + timedelta(days=2))
        db.session.add(po)

        # 20. Lab Orders
        lab_orders = [
            LabOrder(order_number='LAB-2026-105', patient_id=1, doctor_id=1, lab_name='DentCraft Precision Digital CAD/CAM Lab', restoration_type='Zirconia Crown', tooth_numbers='16', shade='A2 / Multi-layer', stage='In Production', due_date=today + timedelta(days=2), cost=2800.0, notes='High translucent zirconia, canine guided occlusion.'),
            LabOrder(order_number='LAB-2026-106', patient_id=2, doctor_id=2, lab_name='Apex 3D Ortho Aligners Bangalore', restoration_type='Clear Aligner Series (Trays 15-20)', tooth_numbers='Upper & Lower Arch', shade='Transparent Clear', stage='Ready', due_date=today, cost=18500.0, notes='Includes attachments template.'),
            LabOrder(order_number='LAB-2026-107', patient_id=5, doctor_id=4, lab_name='DentCraft Precision Digital CAD/CAM Lab', restoration_type='Custom Titanium Abutment + Zirconia Crown', tooth_numbers='36', shade='A3.5', stage='Sent to Lab', due_date=today + timedelta(days=5), cost=7500.0, notes='Screw retained implant restoration.')
        ]
        db.session.add_all(lab_orders)

        # 21. Equipment Maintenance
        equipments = [
            Equipment(name='Dental Operatory Chair 01 (Anthos A3 Plus)', category='Operatory', serial_number='ANT-A3-88219', branch_id=1, last_service_date=today - timedelta(days=60), next_service_due=today + timedelta(days=30), status='Operational', service_vendor='Anthos India Service Care', service_contact='+91 80 4912 0011'),
            Equipment(name='Euronda Class B Vacuum Autoclave (E9 Next 24L)', category='Sterilization', serial_number='EUR-E9-44120', branch_id=1, last_service_date=today - timedelta(days=85), next_service_due=today + timedelta(days=5), status='Operational', service_vendor='Euronda MedEquip', service_contact='+91 80 4912 0022'),
            Equipment(name='Sirona Heliodent Plus Digital RVG Unit', category='Imaging', serial_number='SIR-XRY-99182', branch_id=1, last_service_date=today - timedelta(days=120), next_service_due=today - timedelta(days=5), status='Maintenance Due', service_vendor='Dentsply Sirona Tech Care', service_contact='+91 80 4912 0033'),
            Equipment(name='Cattani Oil-Free Turbo Dental Compressor', category='Compressor', serial_number='CAT-TUR-11029', branch_id=1, last_service_date=today - timedelta(days=40), next_service_due=today + timedelta(days=50), status='Operational', service_vendor='Cattani Air Systems', service_contact='+91 80 4912 0044')
        ]
        db.session.add_all(equipments)

        # 22. Referral Doctors
        referrals = [
            ReferralDoctor(name='Dr. Vikram Mehta (ENT Specialist)', specialty='ENT & Head-Neck Surgeon', clinic_hospital='Fortis Hospital Bannerghatta', phone='+91 98450 77112', email='dr.vmehta@fortis.com', total_referred=18, converted_count=15, total_revenue_generated=185000.0, commission_paid=18500.0),
            ReferralDoctor(name='Dr. Shalini Swaminathan (Pediatrician)', specialty='Consultant Pediatrician', clinic_hospital='Rainbow Children Hospital', phone='+91 98860 33445', email='dr.shalini@rainbow.com', total_referred=24, converted_count=21, total_revenue_generated=142000.0, commission_paid=14200.0),
            ReferralDoctor(name='Dr. Arvind Kulkarni (General Physician)', specialty='Senior Consultant Physician', clinic_hospital='Apollo Clinic Indiranagar', phone='+91 97410 22998', email='arvind.k@apolloclinic.com', total_referred=14, converted_count=11, total_revenue_generated=98000.0, commission_paid=9800.0)
        ]
        db.session.add_all(referrals)

        # 23. Patient Feedback & NPS
        feedback_list = [
            FeedbackNPS(patient_id=1, doctor_id=1, score=10, category='Promoter', comments='Dr. Ananya Sharma was extremely gentle and explained the root canal with digital X-rays step by step. Felt zero pain!', root_cause=None),
            FeedbackNPS(patient_id=2, doctor_id=2, score=10, category='Promoter', comments='Best aligner treatment in Bangalore. My smile transformation is incredible and the 3D preview was spot on.', root_cause=None),
            FeedbackNPS(patient_id=4, doctor_id=3, score=8, category='Passive', comments='Treatment was great, but had to wait 20 minutes past my appointment time in the lounge.', root_cause='Wait time'),
            FeedbackNPS(patient_id=5, doctor_id=4, score=9, category='Promoter', comments='Emergency care was fast and painless. Highly professional setup.', root_cause=None),
            FeedbackNPS(patient_id=6, doctor_id=1, score=10, category='Promoter', comments='Zoom whitening gave instant 7 shade improvement for my wedding. Super happy!', root_cause=None)
        ]
        db.session.add_all(feedback_list)

        # 24. Marketing Campaigns
        campaigns = [
            Campaign(title='6-Month Routine Cleaning Recall Drive', campaign_type='Recall', target_audience='Patients overdue by >180 days (48 patients)', channels='WhatsApp + SMS', status='Ready to Launch', total_targeted=48, sent_count=0, engaged_count=0, appointments_booked=0, estimated_revenue=86400.0),
            Campaign(title='Birthday Smile Gift (₹1,000 Voucher)', campaign_type='Birthday', target_audience='Patients with birthdays this month (14 patients)', channels='WhatsApp', status='Active', total_targeted=14, sent_count=14, engaged_count=9, appointments_booked=6, estimated_revenue=42000.0),
            Campaign(title='Lapsed Patient Win-Back Special', campaign_type='Lapsed Win-back', target_audience='Patients with no visits in 12+ months (32 patients)', channels='WhatsApp + SMS', status='Scheduled', total_targeted=32, sent_count=0, engaged_count=0, appointments_booked=0, estimated_revenue=95000.0),
            Campaign(title='Post-Procedure Google Review Request', campaign_type='Review Request', target_audience='Patients completed treatment in past 48 hours', channels='WhatsApp', status='Active', total_targeted=26, sent_count=26, engaged_count=21, appointments_booked=0, estimated_revenue=0.0)
        ]
        db.session.add_all(campaigns)

        # 25. Staff Shifts
        shifts = [
            StaffShift(doctor_id=1, date=today, shift_type='Full Day (9am - 8pm)', status='Working', notes='Main Operatory Chair 01'),
            StaffShift(doctor_id=2, date=today, shift_type='Morning (9am - 2pm)', status='Working', notes='Orthodontics Operatory Chair 03'),
            StaffShift(doctor_id=3, date=today, shift_type='Full Day (9am - 8pm)', status='Working', notes='Periodontics & Implant Surgery Chair 02'),
            StaffShift(doctor_id=4, date=today, shift_type='Evening (2pm - 8pm)', status='Working', notes='Oral Surgery Consultations Chair 04')
        ]
        db.session.add_all(shifts)

        # 26. Audit Logs
        logs = [
            AuditLog(user_name='Dr. Ananya Sharma', user_role='doctor', action='Updated Tooth #16 Root Canal Clinical Findings & 3D Chart', module='Clinical', ip_address='192.168.1.104', details='Added diagnosis and phase 1 restorative notes.'),
            AuditLog(user_name='Pooja Hegde', user_role='receptionist', action='Checked in Patient Rahul Mehta for Token #014', module='Queue', ip_address='192.168.1.102', details='Assigned to Chair 01 with Dr. Ananya Sharma'),
            AuditLog(user_name='Dr. Rajesh Verma', user_role='admin', action='Generated GST Invoice INV-2026-1029 for ₹17,110', module='Billing', ip_address='192.168.1.101', details='Applied 18% GST (CGST 9% + SGST 9%)'),
            AuditLog(user_name='Pooja Hegde', user_role='receptionist', action='Recorded UPI Payment of ₹14,610 (RCP-2026-904)', module='Billing', ip_address='192.168.1.102', details='Transaction Ref: UPI-948102948201'),
            AuditLog(user_name='Dr. Rohan Patel', user_role='doctor', action='Logged usage of 2x Composite Resin A2 & 1x Mani Bur Pack', module='Inventory', ip_address='192.168.1.105', details='Deducted stock for operative procedure')
        ]
        db.session.add_all(logs)

        db.session.commit()
        print("[SUCCESS] DentiFlow database successfully seeded with realistic Indian dental clinic records!")

if __name__ == '__main__':
    seed_database(reset=os.environ.get('DENTIFLOW_DEMO_RESET') == '1')
