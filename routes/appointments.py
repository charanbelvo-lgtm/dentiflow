from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, Appointment, Patient, Doctor, Chair, QueueToken, AuditLog

appointments_bp = Blueprint('appointments', __name__)

@appointments_bp.route('/appointments')
@login_required
def index():
    doctors = Doctor.query.all()
    chairs = Chair.query.all()
    patients = Patient.query.order_by(Patient.name.asc()).all()
    return render_template('appointments.html', doctors=doctors, chairs=chairs, patients=patients)

@appointments_bp.route('/api/appointments', methods=['GET', 'POST'])
@login_required
def api_appointments():
    if request.method == 'POST':
        data = request.get_json() or request.form
        
        # Calculate appointment number
        count = Appointment.query.count() + 1080
        apt_no = f"APT-{count}"
        
        # Parse date
        apt_date_str = data.get('appointment_date')
        if apt_date_str:
            apt_date = datetime.strptime(apt_date_str, '%Y-%m-%d').date()
        else:
            apt_date = date.today()

        appointment = Appointment(
            appointment_number=apt_no,
            patient_id=int(data.get('patient_id')),
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
        log = AuditLog(
            user_name=current_user.name,
            user_role=current_user.role,
            action=f"Booked appointment {appointment.appointment_number} for {patient.name if patient else ''}",
            module="Appointments",
            ip_address=request.remote_addr or '127.0.0.1'
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Appointment scheduled successfully', 'appointment': appointment.to_dict()}), 201

    # GET filter appointments
    query = Appointment.query
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
            # approximate month filter
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
    log = AuditLog(
        user_name=current_user.name,
        user_role=current_user.role,
        action=f"Updated appointment {apt.appointment_number} status to '{new_status}'",
        module="Appointments",
        ip_address=request.remote_addr or '127.0.0.1'
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'status': 'success', 'message': f'Status updated to {new_status}', 'appointment': apt.to_dict()})
