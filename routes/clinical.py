from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import (
    db, Patient, Doctor, ToothFinding, PeriodontalRecord,
    Prescription, PrescriptionItem, XRayImage, ClinicalNote, AuditLog
)

clinical_bp = Blueprint('clinical', __name__)

@clinical_bp.route('/clinical')
@login_required
def index():
    patients = Patient.query.order_by(Patient.name.asc()).all()
    doctors = Doctor.query.all()
    return render_template('clinical.html', patients=patients, doctors=doctors)

@clinical_bp.route('/dental-chart')
@clinical_bp.route('/chart')
@login_required
def chart():
    patients = Patient.query.order_by(Patient.name.asc()).all()
    return render_template('dental_chart.html', patients=patients)

# 1. Tooth Chart Findings
@clinical_bp.route('/api/patients/<int:patient_id>/teeth', methods=['GET', 'POST'])
@login_required
def patient_teeth(patient_id):
    if request.method == 'POST':
        data = request.get_json()
        tooth_num = int(data.get('tooth_number'))
        
        # Check if tooth finding already exists for this patient
        finding = ToothFinding.query.filter_by(patient_id=patient_id, tooth_number=tooth_num).first()
        if not finding:
            finding = ToothFinding(patient_id=patient_id, tooth_number=tooth_num)
            db.session.add(finding)
            
        finding.status = data.get('status', 'Healthy')
        finding.surfaces = data.get('surfaces', '')
        finding.diagnosis = data.get('diagnosis', '')
        finding.recommended_treatment = data.get('recommended_treatment', '')
        finding.estimated_cost = float(data.get('estimated_cost', 0.0))
        finding.doctor_id = data.get('doctor_id', 1)
        finding.updated_at = datetime.utcnow()

        db.session.commit()

        # Audit log
        log = AuditLog(
            user_name=current_user.name,
            user_role=current_user.role,
            action=f"Updated Tooth #{tooth_num} to '{finding.status}' for Patient #{patient_id}",
            module="Clinical",
            ip_address=request.remote_addr or '127.0.0.1'
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'status': 'success', 'message': f'Tooth #{tooth_num} updated', 'finding': finding.to_dict()})

    findings = ToothFinding.query.filter_by(patient_id=patient_id).all()
    return jsonify({'findings': [f.to_dict() for f in findings]})

# 2. Periodontal Charting
@clinical_bp.route('/api/patients/<int:patient_id>/perio', methods=['GET', 'POST'])
@login_required
def patient_perio(patient_id):
    if request.method == 'POST':
        data = request.get_json()
        records_data = data.get('records', []) # List of tooth perio records

        for rec in records_data:
            tooth_num = int(rec.get('tooth_number'))
            existing = PeriodontalRecord.query.filter_by(patient_id=patient_id, tooth_number=tooth_num).first()
            if not existing:
                existing = PeriodontalRecord(patient_id=patient_id, tooth_number=tooth_num)
                db.session.add(existing)

            existing.pocket_depth_mb = int(rec.get('pocket_depth_mb', 2))
            existing.pocket_depth_b = int(rec.get('pocket_depth_b', 2))
            existing.pocket_depth_db = int(rec.get('pocket_depth_db', 2))
            existing.pocket_depth_ml = int(rec.get('pocket_depth_ml', 2))
            existing.pocket_depth_l = int(rec.get('pocket_depth_l', 2))
            existing.pocket_depth_dl = int(rec.get('pocket_depth_dl', 2))
            existing.bleeding_on_probing = bool(rec.get('bleeding_on_probing', False))
            existing.mobility = str(rec.get('mobility', '0'))
            existing.gingival_margin = int(rec.get('gingival_margin', 0))
            existing.recorded_at = datetime.utcnow()

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Periodontal chart recorded successfully'})

    records = PeriodontalRecord.query.filter_by(patient_id=patient_id).all()
    return jsonify({'records': [r.to_dict() for r in records]})

# 3. AI Voice-to-Notes SOAP Generator & Saver
@clinical_bp.route('/api/patients/<int:patient_id>/voice-notes', methods=['POST'])
@login_required
def save_voice_notes(patient_id):
    data = request.get_json()
    raw_transcript = data.get('raw_transcript', '')
    
    # Intelligent parsing mock or manual fields
    subjective = data.get('subjective') or f"Patient reports: {raw_transcript}"
    objective = data.get('objective') or "Intraoral inspection reveals localized erythema and restoration wear. Vitals normal."
    assessment = data.get('assessment') or "Suspected symptomatic pulpitis / initial marginal breakdown."
    plan = data.get('plan') or "Schedule follow-up for diagnostic IOPA radiograph and restorative restoration."

    note = ClinicalNote(
        patient_id=patient_id,
        doctor_id=data.get('doctor_id', 1),
        subjective=subjective,
        objective=objective,
        assessment=assessment,
        plan=plan,
        is_ai_draft=bool(data.get('is_ai_draft', True)),
        raw_transcript=raw_transcript
    )
    db.session.add(note)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Clinical note saved successfully', 'note': note.to_dict()})

# 4. Digital Prescriptions
@clinical_bp.route('/api/patients/<int:patient_id>/prescriptions', methods=['GET', 'POST'])
@login_required
def patient_prescriptions(patient_id):
    if request.method == 'POST':
        data = request.get_json()
        count = Prescription.query.count() + 90
        rx_no = f"RX-2026-{str(count).zfill(3)}"

        prescription = Prescription(
            rx_number=rx_no,
            patient_id=patient_id,
            doctor_id=int(data.get('doctor_id', 1)),
            diagnosis=data.get('diagnosis', 'Post-procedure analgesia & antibiotic prophylaxis'),
            general_advice=data.get('general_advice', 'Take with plenty of water. Maintain oral hygiene.')
        )
        db.session.add(prescription)
        db.session.commit()

        # Add items
        items_data = data.get('items', [])
        for item in items_data:
            rx_item = PrescriptionItem(
                prescription_id=prescription.id,
                medicine_name=item.get('medicine_name'),
                dosage=item.get('dosage', '1 Tablet'),
                frequency=item.get('frequency', 'Twice daily (1-0-1)'),
                duration=item.get('duration', '3 days'),
                instructions=item.get('instructions', 'After food')
            )
            db.session.add(rx_item)

        db.session.commit()

        # Audit log
        log = AuditLog(
            user_name=current_user.name,
            user_role=current_user.role,
            action=f"Created Prescription {prescription.rx_number} for Patient #{patient_id}",
            module="Clinical",
            ip_address=request.remote_addr or '127.0.0.1'
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Prescription issued', 'prescription': prescription.to_dict()})

    rx_list = Prescription.query.filter_by(patient_id=patient_id).order_by(Prescription.id.desc()).all()
    return jsonify({'prescriptions': [r.to_dict() for r in rx_list]})

# Printable view for prescription
@clinical_bp.route('/prescriptions/<int:rx_id>/print')
@login_required
def print_prescription(rx_id):
    rx = Prescription.query.get_or_404(rx_id)
    return render_template('print_prescription.html', prescription=rx)
