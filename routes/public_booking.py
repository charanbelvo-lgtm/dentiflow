from datetime import datetime, date
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, abort
from flask_login import current_user
from models import db, Appointment, Patient, Doctor, TreatmentMaster, QueueToken, Branch, Chair
from security import log_audit_event, normalize_role
from firebase_service import sync_patient_to_firestore, sync_appointment_to_firestore, sync_queue_token_to_firestore

public_bp = Blueprint('public', __name__)

def parse_appointment_date(data):
    apt_date_raw = data.get('appointment_date') or data.get('date') or data.get('appointmentDate')
    if isinstance(apt_date_raw, date):
        return apt_date_raw
    if isinstance(apt_date_raw, datetime):
        return apt_date_raw.date()
    if apt_date_raw and isinstance(apt_date_raw, str):
        cleaned = apt_date_raw.strip()
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%d %b %Y', '%d %B %Y', '%m/%d/%Y'):
            try:
                return datetime.strptime(cleaned, fmt).date()
            except ValueError:
                continue
    return date.today()

def process_booking(data, patient_user=None):
    name = (data.get('name') or '').strip()
    phone = (data.get('phone') or '').strip()
    email = (data.get('email') or '').strip().lower()

    if patient_user and patient_user.is_authenticated:
        if not email:
            email = (patient_user.email or '').strip().lower()
        if not name:
            name = (patient_user.name or '').strip()

    if not name or not phone:
        return None, None, 'Name and phone number are required.'
    
    # Resolve Doctor by ID or Name
    doctor_input = data.get('doctor_id') or data.get('doctor') or 1
    doctor = None
    try:
        doc_id_int = int(doctor_input)
        doctor = Doctor.query.get(doc_id_int)
    except (ValueError, TypeError):
        doc_name_str = str(doctor_input).strip()
        doctor = Doctor.query.filter(Doctor.name.ilike(f"%{doc_name_str}%")).first()

    if not doctor:
        doctor = Doctor.query.first()
    doctor_id = doctor.id if doctor else 1
        
    treatment_name = data.get('treatment_name') or data.get('category') or 'General Consultation'
    apt_date = parse_appointment_date(data)
    start_time = data.get('start_time') or data.get('time') or '10:30 AM'
    if len(start_time) <= 5 and ':' in start_time:
        # Convert HH:MM to HH:MM AM/PM
        try:
            start_time = datetime.strptime(start_time, '%H:%M').strftime('%I:%M %p')
        except ValueError:
            pass

    # Find patient by email first, then phone
    patient = None
    if email:
        patient = Patient.query.filter_by(email=email).first()
    if not patient and phone:
        patient = Patient.query.filter_by(phone=phone).first()

    if not patient:
        last_pt = Patient.query.order_by(Patient.id.desc()).first()
        next_pt_num = (last_pt.id + 1) if last_pt else 1
        patient_id_code = f"DF-2026-{str(next_pt_num).zfill(3)}"
        while Patient.query.filter_by(patient_id=patient_id_code).first():
            next_pt_num += 1
            patient_id_code = f"DF-2026-{str(next_pt_num).zfill(3)}"

        patient = Patient(
            patient_id=patient_id_code,
            name=name,
            phone=phone,
            email=email if email else None,
            age=int(data.get('age', 28) or 28),
            gender=data.get('gender', 'Male'),
            primary_doctor_id=doctor_id,
            branch_id=1
        )
        db.session.add(patient)
        db.session.commit()
    else:
        # Update contact info if missing
        if email and not patient.email:
            patient.email = email
        if phone and not patient.phone:
            patient.phone = phone
        db.session.commit()

    # Determine assigned chair based on doctor specialty
    chair_id = 1
    if doctor and doctor.assigned_chair:
        ch = Chair.query.filter_by(chair_number=doctor.assigned_chair).first()
        if ch:
            chair_id = ch.id
        elif '02' in doctor.assigned_chair:
            chair_id = 2
        elif '03' in doctor.assigned_chair:
            chair_id = 3
        elif '04' in doctor.assigned_chair:
            chair_id = 4

    # Create Appointment with guaranteed unique appointment_number
    last_apt = Appointment.query.order_by(Appointment.id.desc()).first()
    next_apt_num = (last_apt.id + 1081) if last_apt else 1081
    apt_no = f"APT-{next_apt_num}"
    while Appointment.query.filter_by(appointment_number=apt_no).first():
        next_apt_num += 1
        apt_no = f"APT-{next_apt_num}"

    appointment = Appointment(
        appointment_number=apt_no,
        patient_id=patient.id,
        doctor_id=doctor_id,
        chair_id=chair_id,
        branch_id=1,
        appointment_date=apt_date,
        start_time=start_time,
        duration_minutes=30,
        procedure_name=treatment_name,
        status='Confirmed',
        booking_source='Online Portal',
        deposit_amount=0.0,
        notes="Booked by patient via DentiFlow Patient Portal."
    )
    db.session.add(appointment)
    db.session.commit()

    # Calculate real waiting tokens ahead for this doctor
    waiting_ahead = QueueToken.query.filter_by(doctor_id=doctor_id, status='Waiting').count()
    estimated_wait = max(15, (waiting_ahead + 1) * 15)
    last_tok = QueueToken.query.order_by(QueueToken.id.desc()).first()
    next_tok_num = (last_tok.id + 1) if last_tok else 1
    token_str = f"Token #{str(next_tok_num).zfill(2)}"
    while QueueToken.query.filter_by(token_number=token_str).first():
        next_tok_num += 1
        token_str = f"Token #{str(next_tok_num).zfill(2)}"

    token = QueueToken(
        appointment_id=appointment.id,
        patient_id=patient.id,
        token_number=token_str,
        doctor_id=doctor_id,
        chair_id=chair_id,
        procedure_name=treatment_name,
        status='Waiting',
        is_emergency=False,
        estimated_wait_min=estimated_wait
    )
    db.session.add(token)
    db.session.commit()

    # Update patient next appointment
    try:
        clean_time = start_time.split()[0]
        if len(clean_time) <= 5:
            t_obj = datetime.strptime(clean_time, "%H:%M").time() if ':' in clean_time else datetime.now().time()
        else:
            t_obj = datetime.now().time()
        apt_dt = datetime.combine(apt_date, t_obj)
        patient.next_appointment = apt_dt
        db.session.commit()
    except Exception:
        pass

    # Cloud Firestore Sync
    sync_patient_to_firestore(patient.to_dict())
    sync_appointment_to_firestore(appointment.to_dict())
    sync_queue_token_to_firestore(token.to_dict())

    log_audit_event(
        action=f"Patient booking confirmed: {appointment.appointment_number} for {patient.name} ({patient.phone}) on {appointment.appointment_date.strftime('%Y-%m-%d')}",
        module="Patient Booking",
        user_name=patient.name,
        user_role="patient"
    )

    return appointment, token, None


@public_bp.route('/book', methods=['GET', 'POST'])
def booking_page():
    # Enforce patient authentication
    if not current_user.is_authenticated:
        if request.is_json:
            return jsonify({'status': 'error', 'message': 'Authentication required. Please sign in as a patient.'}), 401
        flash('Please sign in or create an account as a patient to book an appointment.', 'info')
        return redirect(url_for('auth.login', next=url_for('public.booking_page'), role='patient'))

    # Strictly reject non-patient roles
    user_role = normalize_role(getattr(current_user, 'role', ''))
    if user_role != 'patient':
        log_audit_event(
            action=f"ACCESS_DENIED: {current_user.name} ({user_role}) denied access to patient booking workflow",
            module="Authorization"
        )
        if request.is_json:
            return jsonify({'status': 'error', 'message': 'Access forbidden: Appointment booking is reserved for patients.'}), 403
        abort(403)

    doctors = Doctor.query.all()
    treatments = TreatmentMaster.query.all()
    branches = Branch.query.all()
    patient = Patient.query.filter_by(email=current_user.email).first()

    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        appointment, token, error = process_booking(data, patient_user=current_user)
        if error:
            if request.is_json:
                return jsonify({'status': 'error', 'message': error}), 400
            return render_template('booking.html', doctors=doctors, treatments=treatments, branches=branches, patient=patient, error=error)
        
        flash(f"Appointment {appointment.appointment_number} confirmed! Scheduled with {appointment.doctor.name if appointment.doctor else 'Doctor'} on {appointment.appointment_date.strftime('%d %b %Y')} at {appointment.start_time}.", 'success')

        if request.is_json:
            return jsonify({
                'status': 'success',
                'message': 'Your appointment has been confirmed!',
                'redirect': url_for('dashboard.index'),
                'appointment_id': appointment.id,
                'appointment_number': appointment.appointment_number,
                'patient_name': appointment.patient.name,
                'doctor_name': appointment.doctor.name if appointment.doctor else 'Dr. Ananya Sharma',
                'procedure': appointment.procedure_name,
                'date': appointment.appointment_date.strftime('%d %b %Y'),
                'appointment_date': appointment.appointment_date.strftime('%Y-%m-%d'),
                'time': appointment.start_time,
                'token_number': token.token_number if token else 'Token #01',
                'estimated_wait_min': token.estimated_wait_min if token else 15,
                'wait_time': f"{token.estimated_wait_min if token else 15} mins",
                'chair': appointment.chair.name if appointment.chair else 'Chair 01',
                'status': 'success',
                'appointment_status': appointment.status
            }), 201

        # Redirect patient immediately back to Patient Dashboard!
        return redirect(url_for('dashboard.index'))

    return render_template('booking.html', doctors=doctors, treatments=treatments, branches=branches, patient=patient)


@public_bp.route('/portal')
def patient_portal():
    if not current_user.is_authenticated:
        flash('Please sign in as a patient to access the patient portal.', 'info')
        return redirect(url_for('auth.login', role='patient'))

    if current_user.role != 'patient':
        log_audit_event(
            action=f"ACCESS_DENIED: {current_user.name} ({current_user.role}) denied access to patient portal",
            module="Authorization"
        )
        abort(403)

    return redirect(url_for('dashboard.index'))


@public_bp.route('/api/public/book', methods=['POST'])
@public_bp.route('/api/book-and-wait', methods=['POST'])
def public_book():
    if not current_user.is_authenticated:
        return jsonify({'status': 'error', 'message': 'Authentication required. Please sign in as a patient.'}), 401

    user_role = normalize_role(getattr(current_user, 'role', ''))
    if user_role != 'patient':
        log_audit_event(
            action=f"ACCESS_DENIED: {current_user.name} ({user_role}) denied access to patient booking API",
            module="Authorization"
        )
        return jsonify({'status': 'error', 'message': 'Access forbidden: Appointment booking is reserved for patients.'}), 403

    data = request.get_json() if request.is_json else request.form
    appointment, token, error = process_booking(data, patient_user=current_user)
    if error:
        return jsonify({'status': 'error', 'message': error}), 400

    flash(f"Appointment {appointment.appointment_number} confirmed successfully!", 'success')

    waiting_position = QueueToken.query.filter(
        QueueToken.doctor_id == appointment.doctor_id,
        QueueToken.status == 'Waiting',
        QueueToken.id <= (token.id if token else 999999)
    ).count()

    return jsonify({
        'status': 'success',
        'message': 'Your appointment has been confirmed!',
        'redirect': url_for('dashboard.index'),
        'appointment_id': appointment.id,
        'appointment_number': appointment.appointment_number,
        'patient_name': appointment.patient.name,
        'doctor_name': appointment.doctor.name if appointment.doctor else 'Dr. Ananya Sharma',
        'procedure': appointment.procedure_name,
        'date': appointment.appointment_date.strftime('%d %b %Y'),
        'appointment_date': appointment.appointment_date.strftime('%Y-%m-%d'),
        'time': appointment.start_time,
        'token_number': token.token_number if token else 'Token #01',
        'estimated_wait_min': token.estimated_wait_min if token else 15,
        'wait_time': f"{token.estimated_wait_min if token else 15} mins",
        'queue_position': waiting_position if waiting_position > 0 else 1,
        'chair': appointment.chair.name if appointment.chair else 'Chair 01',
        'status': 'success',
        'appointment_status': appointment.status
    }), 201


@public_bp.route('/api/patient/wait-time', methods=['GET'])
def get_patient_wait_time():
    if not current_user.is_authenticated:
        return jsonify({'status': 'error', 'message': 'Authentication required.'}), 401

    patient = Patient.query.filter_by(email=current_user.email).first()
    if not patient:
        return jsonify({'status': 'error', 'message': 'Patient record not found.'}), 404

    today = date.today()
    all_apts = Appointment.query.filter_by(patient_id=patient.id).all()
    upcoming = [a for a in all_apts if a.appointment_date >= today]
    upcoming.sort(key=lambda a: (a.appointment_date, a.start_time))
    active_apt = upcoming[0] if upcoming else (sorted(all_apts, key=lambda a: a.id, reverse=True)[0] if all_apts else None)

    token = None
    if active_apt:
        token = QueueToken.query.filter_by(appointment_id=active_apt.id).first()
        if not token:
            token = QueueToken.query.filter_by(patient_id=patient.id, status='Waiting').order_by(QueueToken.id.desc()).first()

    waiting_count = QueueToken.query.filter(
        QueueToken.doctor_id == (active_apt.doctor_id if active_apt else 1),
        QueueToken.status == 'Waiting'
    ).count()

    return jsonify({
        'status': 'success',
        'has_appointment': bool(active_apt),
        'appointment_number': active_apt.appointment_number if active_apt else None,
        'procedure': active_apt.procedure_name if active_apt else None,
        'doctor_name': active_apt.doctor.name if active_apt and active_apt.doctor else 'Dr. Ananya Sharma',
        'date': active_apt.appointment_date.strftime('%d %b %Y') if active_apt else None,
        'appointment_date': active_apt.appointment_date.strftime('%Y-%m-%d') if active_apt else None,
        'time': active_apt.start_time if active_apt else None,
        'token_number': token.token_number if token else (f"Token #{str(waiting_count + 1).zfill(2)}" if active_apt else 'Token #01'),
        'estimated_wait_min': token.estimated_wait_min if token else (max(15, waiting_count * 15) if active_apt else 0),
        'wait_time': f"{token.estimated_wait_min if token else (max(15, waiting_count * 15) if active_apt else 0)} mins",
        'queue_position': waiting_count if waiting_count > 0 else 1,
        'chair': active_apt.chair.name if active_apt and active_apt.chair else 'Chair 01',
        'appointment_status': active_apt.status if active_apt else None
    })



