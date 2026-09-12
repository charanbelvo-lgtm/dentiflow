from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from models import db, Appointment, Patient, Doctor, Chair, QueueToken, AuditLog
from security import log_audit_event, staff_required, normalize_role

appointments_bp = Blueprint('appointments', __name__)

@appointments_bp.route('/appointments')
@login_required
def index():
    doctors = Doctor.query.all()
    chairs = Chair.query.all()
    today = date.today()
    user_role = normalize_role(getattr(current_user, 'role', ''))

    if user_role == 'patient':
        patient = Patient.query.filter_by(email=current_user.email).first()
        patients = [patient] if patient else []
        appointments = Appointment.query.filter_by(patient_id=patient.id)\
            .order_by(Appointment.appointment_date.desc(), Appointment.start_time.desc()).all() if patient else []
    else:
        patients = Patient.query.order_by(Patient.name.asc()).all()
        appointments = Appointment.query.order_by(Appointment.appointment_date.desc(), Appointment.start_time.desc()).all()

    # Calculate real stats
    todays_visits = sum(1 for a in appointments if a.appointment_date == today)
    if todays_visits == 0:
        todays_visits = len(appointments)
    completed = sum(1 for a in appointments if a.status == 'Completed')
    in_queue = sum(1 for a in appointments if a.status in ['Waiting', 'Checked In', 'In Progress', 'Confirmed'])
    rescheduled = sum(1 for a in appointments if a.status == 'Rescheduled')

    stats = {
        'todays_visits': todays_visits,
        'completed': completed,
        'in_queue': in_queue,
        'rescheduled': rescheduled
    }

    return render_template(
        'appointments.html',
        doctors=doctors,
        chairs=chairs,
        patients=patients,
        appointments=appointments,
        stats=stats
    )


@appointments_bp.route('/api/appointments', methods=['GET', 'POST'])
@login_required
def api_appointments():
    user_role = normalize_role(getattr(current_user, 'role', ''))

    if request.method == 'POST':
        data = request.get_json() or request.form
        
        # Calculate guaranteed unique appointment number
        count = Appointment.query.count() + 1
        while True:
            apt_no = f"APT-{1080 + count}"
            if not Appointment.query.filter_by(appointment_number=apt_no).first():
                break
            count += 1
        
        # Determine patient_id
        if user_role == 'patient':
            patient = Patient.query.filter_by(email=current_user.email).first()
            if not patient:
                return jsonify({'status': 'error', 'message': 'Patient record not found.'}), 404
            patient_id = patient.id
        else:
            patient_id = int(data.get('patient_id'))

        # Parse date robustly
        apt_date_raw = data.get('appointment_date') or data.get('date') or data.get('appointmentDate')
        apt_date = None
        if isinstance(apt_date_raw, date):
            apt_date = apt_date_raw
        elif isinstance(apt_date_raw, datetime):
            apt_date = apt_date_raw.date()
        elif apt_date_raw and isinstance(apt_date_raw, str):
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%d %b %Y', '%d %B %Y', '%m/%d/%Y'):
                try:
                    apt_date = datetime.strptime(apt_date_raw.strip(), fmt).date()
                    break
                except ValueError:
                    continue
        if not apt_date:
            apt_date = date.today()

        appointment = Appointment(
            appointment_number=apt_no,
            patient_id=patient_id,
            doctor_id=int(data.get('doctor_id', 1)),
            chair_id=int(data.get('chair_id', 1)) if data.get('chair_id') else None,
            branch_id=int(data.get('branch_id', 1)),
            appointment_date=apt_date,
            start_time=data.get('start_time', '10:00 AM'),
            duration_minutes=int(data.get('duration_minutes', 30)),
            procedure_name=data.get('procedure_name', 'General Dental Consultation'),
            status=data.get('status', 'Confirmed'),
            booking_source=data.get('booking_source', 'Walk-in'),
            deposit_amount=float(data.get('deposit_amount', 0.0)),
            reminder_preference=data.get('reminder_preference', 'WhatsApp + SMS'),
            notes=data.get('notes'),
            is_emergency=bool(data.get('is_emergency', False))
        )
        db.session.add(appointment)
        db.session.commit()

        # If status is Waiting or today's appointment with immediate check-in, create queue token
        if appointment.status == 'Waiting' or data.get('auto_checkin'):
            token_count = QueueToken.query.count() + 14
            token = QueueToken(
                appointment_id=appointment.id,
                patient_id=appointment.patient_id,
                token_number=f"Token #{str(token_count).zfill(3)}",
                doctor_id=appointment.doctor_id,
                chair_id=appointment.chair_id,
                procedure_name=appointment.procedure_name,
                status='Waiting',
                is_emergency=appointment.is_emergency,
                estimated_wait_min=15
            )
            db.session.add(token)
            db.session.commit()

        # Audit log
        patient = Patient.query.get(appointment.patient_id)
        log_audit_event(
            action=f"Booked appointment {appointment.appointment_number} for {patient.name if patient else ''}",
            module="Appointments",
            details=f"Apt No: {appointment.appointment_number}, Doctor: {appointment.doctor_id}, Date: {appointment.appointment_date}"
        )

        return jsonify({'status': 'success', 'message': 'Appointment scheduled successfully', 'appointment': appointment.to_dict()}), 201

    # GET filter appointments
    query = Appointment.query
    if user_role == 'patient':
        patient = Patient.query.filter_by(email=current_user.email).first()
        if not patient:
            return jsonify({'appointments': []})
        query = query.filter_by(patient_id=patient.id)

    date_str = request.args.get('date')
    doctor_id = request.args.get('doctor_id')
    chair_id = request.args.get('chair_id')
    status = request.args.get('status')
    view_mode = request.args.get('view', 'day') # day, week, month

    if date_str:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if view_mode == 'day':
            query = query.filter_by(appointment_date=target_date)
        elif view_mode == 'week':
            start_of_week = target_date - timedelta(days=target_date.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            query = query.filter(Appointment.appointment_date >= start_of_week, Appointment.appointment_date <= end_of_week)
        elif view_mode == 'month':
            start_of_month = target_date.replace(day=1)
            query = query.filter(Appointment.appointment_date >= start_of_month, Appointment.appointment_date <= start_of_month + timedelta(days=31))

    if doctor_id:
        query = query.filter_by(doctor_id=int(doctor_id))
    if chair_id:
        query = query.filter_by(chair_id=int(chair_id))
    if status:
        query = query.filter_by(status=status)

    appointments = query.order_by(Appointment.appointment_date.asc(), Appointment.start_time.asc()).all()
    return jsonify({'appointments': [a.to_dict() for a in appointments]})

@appointments_bp.route('/api/appointments/<int:appointment_id>/status', methods=['POST'])
@login_required
def update_appointment_status(appointment_id):
    apt = Appointment.query.get_or_404(appointment_id)
    data = request.get_json()
    new_status = data.get('status') # Waiting, In Treatment, Completed, Cancelled, Rescheduled
    
    if current_user.role == 'patient':
        patient = Patient.query.filter_by(email=current_user.email).first()
        if not patient or apt.patient_id != patient.id:
            return jsonify({'status': 'error', 'message': 'Access forbidden: unauthorized appointment.'}), 403
        if new_status != 'Cancelled':
            return jsonify({'status': 'error', 'message': 'Patients are only permitted to cancel their appointments.'}), 403

    apt.status = new_status

    # Chair updates
    if apt.chair_id:
        chair = Chair.query.get(apt.chair_id)
        if chair:
            if new_status == 'In Treatment':
                chair.status = 'In Treatment'
                chair.current_patient = apt.patient.name if apt.patient else 'Patient'
                chair.current_doctor = apt.doctor.name if apt.doctor else 'Doctor'
                chair.current_procedure = apt.procedure_name
                chair.session_start_time = datetime.utcnow()
            elif new_status == 'Completed':
                chair.status = 'Cleaning'
                chair.current_patient = None
                chair.current_doctor = None
                chair.current_procedure = None
            elif new_status == 'Cancelled':
                if chair.current_patient == (apt.patient.name if apt.patient else ''):
                    chair.status = 'Available'
                    chair.current_patient = None

    # Handle queue token
    token = QueueToken.query.filter_by(appointment_id=apt.id).first()
    if new_status == 'Waiting' and not token:
        token_count = QueueToken.query.count() + 14
        token = QueueToken(
            appointment_id=apt.id,
            patient_id=apt.patient_id,
            token_number=f"Token #{str(token_count).zfill(3)}",
            doctor_id=apt.doctor_id,
            chair_id=apt.chair_id,
            procedure_name=apt.procedure_name,
            status='Waiting',
            is_emergency=apt.is_emergency,
            estimated_wait_min=10
        )
        db.session.add(token)
    elif token:
        if new_status == 'In Treatment':
            token.status = 'Serving'
            token.called_at = datetime.utcnow()
        elif new_status == 'Completed':
            token.status = 'Completed'
        elif new_status == 'Cancelled':
            token.status = 'Skipped'

    # Reschedule support
    if new_status == 'Rescheduled' and data.get('new_date'):
        apt.appointment_date = datetime.strptime(data['new_date'], '%Y-%m-%d').date()
        if data.get('new_time'):
            apt.start_time = data['new_time']
        apt.status = 'Confirmed'

    db.session.commit()

    # Log audit
    log_audit_event(
        action=f"Updated appointment {apt.appointment_number} status to '{new_status}'",
        module="Appointments",
        details=f"Appointment: {apt.appointment_number}, New Status: {new_status}"
    )

    return jsonify({'status': 'success', 'message': f'Status updated to {new_status}', 'appointment': apt.to_dict()})
