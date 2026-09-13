from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from models import (
    db, Patient, MedicalAlert, FamilyMember, PatientDocument,
    Appointment, ToothFinding, PeriodontalRecord, Prescription,
    TreatmentPlan, Invoice, XRayImage, ClinicalNote, Doctor, AuditLog
)
from firebase_service import sync_patient_to_firestore

patients_bp = Blueprint('patients', __name__)

@patients_bp.route('/patients')
@login_required
def index():
    doctors = Doctor.query.all()
    patients = Patient.query.order_by(Patient.id.desc()).limit(50).all()
    return render_template('patients.html', doctors=doctors, patients=patients)

@patients_bp.route('/patients/<int:patient_id>')
@login_required
def detail(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if current_user.role == 'patient' and patient.email != current_user.email:
        abort(403)
    doctors = Doctor.query.all()
    return render_template('patient_detail.html', patient=patient, doctors=doctors)

@patients_bp.route('/api/patients', methods=['GET', 'POST'])
@login_required
def api_patients():
    if request.method == 'POST':
        data = request.get_json() or request.form
        
        # Generate unique patient ID
        last_pt = Patient.query.order_by(Patient.id.desc()).first()
        next_pt_num = (last_pt.id + 1) if last_pt else 1
        new_patient_id = f"DF-2026-{str(next_pt_num).zfill(3)}"
        while Patient.query.filter_by(patient_id=new_patient_id).first():
            next_pt_num += 1
            new_patient_id = f"DF-2026-{str(next_pt_num).zfill(3)}"
        
        patient = Patient(
            patient_id=new_patient_id,
            name=data.get('name'),
            age=int(data.get('age', 30)),
            gender=data.get('gender', 'Male'),
            phone=data.get('phone'),
            email=data.get('email'),
            blood_group=data.get('blood_group', 'B+'),
            address=data.get('address'),
            emergency_contact_name=data.get('emergency_contact_name'),
            emergency_contact_phone=data.get('emergency_contact_phone'),
            primary_doctor_id=data.get('primary_doctor_id', 1),
            branch_id=data.get('branch_id', 1),
            abdm_health_id=data.get('abdm_health_id'),
            insurance_policy_no=data.get('insurance_policy_no'),
            insurance_provider=data.get('insurance_provider'),
            outstanding_balance=0.0,
            total_spent=0.0
        )
        db.session.add(patient)
        db.session.commit()

        # Add medical alert if specified
        if data.get('medical_alert'):
            alert = MedicalAlert(
                patient_id=patient.id,
                alert_type='Medical Note',
                alert_text=data.get('medical_alert'),
                is_critical=True
            )
            db.session.add(alert)
            db.session.commit()

        # Log audit
        log = AuditLog(
            user_name=current_user.name,
            user_role=current_user.role,
            action=f"Added new patient {patient.name} ({patient.patient_id})",
            module="Patient",
            ip_address=request.remote_addr or '127.0.0.1'
        )
        db.session.add(log)
        db.session.commit()

        patient_dict = patient.to_dict()
        sync_patient_to_firestore(patient_dict)

        return jsonify({'status': 'success', 'message': 'Patient added successfully', 'patient': patient_dict}), 201

    # GET with search, filter, sort
    query = Patient.query
    search = request.args.get('search', '').strip()
    doctor_id = request.args.get('doctor_id')
    blood_group = request.args.get('blood_group')

    if search:
        query = query.filter(
            (Patient.name.ilike(f'%{search}%')) |
            (Patient.phone.ilike(f'%{search}%')) |
            (Patient.patient_id.ilike(f'%{search}%'))
        )
    if doctor_id:
        query = query.filter_by(primary_doctor_id=int(doctor_id))
    if blood_group:
        query = query.filter_by(blood_group=blood_group)

    patients = query.order_by(Patient.id.desc()).all()
    return jsonify({'patients': [p.to_dict() for p in patients], 'total': len(patients)})

@patients_bp.route('/api/patients/<int:patient_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_patient_detail(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if current_user.role == 'patient' and patient.email != current_user.email:
        return jsonify({'status': 'error', 'message': 'You can only access your own record.'}), 403
    
    if request.method == 'PUT':
        data = request.get_json()
        for field in ['name', 'age', 'gender', 'phone', 'email', 'blood_group', 'address', 'abdm_health_id', 'insurance_policy_no', 'insurance_provider']:
            if field in data:
                setattr(patient, field, data[field])
        if 'primary_doctor_id' in data:
            patient.primary_doctor_id = int(data['primary_doctor_id'])
            
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Patient updated successfully', 'patient': patient.to_dict()})

    # Detailed bundle
    alerts = [a.to_dict() for a in patient.medical_alerts]
    family = [f.to_dict() for f in patient.family_members]
    documents = [d.to_dict() for d in patient.documents]
    appointments = [a.to_dict() for a in patient.appointments]
    teeth = [t.to_dict() for t in patient.tooth_findings]
    perio = [p.to_dict() for p in patient.periodontal_records]
    xrays = [x.to_dict() for x in patient.xrays]
    prescriptions = [rx.to_dict() for rx in patient.prescriptions]
    treatment_plans = [tp.to_dict() for tp in patient.treatment_plans]
    invoices = [inv.to_dict() for inv in patient.invoices]
    clinical_notes = [cn.to_dict() for cn in patient.clinical_notes]

    # Chronological Timeline
    timeline_events = []
    for a in appointments:
        timeline_events.append({
            'type': 'appointment',
            'date': a['appointment_date'],
            'title': f"Appointment: {a['procedure_name']}",
            'subtitle': f"Dr. {a['doctor_name']} • {a['status']}",
            'icon': 'fa-calendar-check',
            'color': '#2563EB'
        })
    for rx in prescriptions:
        timeline_events.append({
            'type': 'prescription',
            'date': rx['date_formatted'],
            'title': f"Prescription: {rx['rx_number']}",
            'subtitle': f"By {rx['doctor_name']} ({len(rx['items'])} items)",
            'icon': 'fa-prescription',
            'color': '#10B981'
        })
    for cn in clinical_notes:
        timeline_events.append({
            'type': 'clinical_note',
            'date': cn['date_formatted'],
            'title': f"Clinical Note (SOAP)",
            'subtitle': f"{cn['assessment'] or 'Clinical examination completed'}",
            'icon': 'fa-notes-medical',
            'color': '#8B5CF6'
        })
    for inv in invoices:
        timeline_events.append({
            'type': 'invoice',
            'date': inv['date_only'],
            'title': f"Invoice Generated: {inv['invoice_number']} (₹{inv['total_amount']:,.0f})",
            'subtitle': f"Status: {inv['status']} • Paid: ₹{inv['paid_amount']:,.0f}",
            'icon': 'fa-receipt',
            'color': '#F59E0B'
        })

    return jsonify({
        'patient': patient.to_dict(),
        'alerts': alerts,
        'family': family,
        'documents': documents,
        'appointments': appointments,
        'teeth': teeth,
        'perio': perio,
        'xrays': xrays,
        'prescriptions': prescriptions,
        'treatment_plans': treatment_plans,
        'invoices': invoices,
        'clinical_notes': clinical_notes,
        'timeline': timeline_events
    })

@patients_bp.route('/api/patients/<int:patient_id>/alerts', methods=['POST'])
@login_required
def add_patient_alert(patient_id):
    data = request.get_json()
    alert = MedicalAlert(
        patient_id=patient_id,
        alert_type=data.get('alert_type', 'Allergy'),
        alert_text=data.get('alert_text', ''),
        is_critical=data.get('is_critical', True)
    )
    db.session.add(alert)
    db.session.commit()
    return jsonify({'status': 'success', 'alert': alert.to_dict()})

@patients_bp.route('/api/patients/<int:patient_id>/family', methods=['POST'])
@login_required
def add_patient_family(patient_id):
    data = request.get_json()
    member = FamilyMember(
        patient_id=patient_id,
        name=data.get('name'),
        relation=data.get('relation'),
        phone=data.get('phone'),
        age=int(data.get('age', 0)) if data.get('age') else None
    )
    db.session.add(member)
    db.session.commit()
    return jsonify({'status': 'success', 'family_member': member.to_dict()})

@patients_bp.route('/api/patients/<int:patient_id>/upload', methods=['POST'])
@login_required
def upload_document(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    doc_type = request.form.get('doc_type', 'Consent Form')
    title = request.form.get('title', 'Patient Document')
    folder = 'xrays' if doc_type in ['X-Ray', 'OPG', 'RVG', 'CBCT'] else 'documents'

    file_obj = request.files.get('file')
    if not file_obj:
        return jsonify({'status': 'error', 'message': 'No file was provided for upload.'}), 400

    from firebase_service import upload_patient_file
    upload_res = upload_patient_file(file_obj, patient_id=patient.id, folder=folder, filename=file_obj.filename)

    file_size_str = f"{max(0.1, round(file_obj.tell() / (1024 * 1024), 1))} MB" if hasattr(file_obj, 'tell') else "1.2 MB"

    if folder == 'xrays':
        xray = XRayImage(
            patient_id=patient.id,
            title=title,
            xray_type=doc_type,
            image_url=upload_res['url'],
            ai_cavity_detected=False,
            ai_confidence=95.0,
            ai_analysis_notes="Radiograph uploaded successfully. Clear coronal margin visible."
        )
        db.session.add(xray)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': f'Radiograph uploaded ({upload_res["storage"]})',
            'xray': xray.to_dict(),
            'storage': upload_res['storage']
        })
    else:
        doc = PatientDocument(
            patient_id=patient.id,
            title=title,
            doc_type=doc_type,
            file_url=upload_res['url'],
            file_size=file_size_str
        )
        db.session.add(doc)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': f'Document uploaded ({upload_res["storage"]})',
            'document': doc.to_dict(),
            'storage': upload_res['storage']
        })
