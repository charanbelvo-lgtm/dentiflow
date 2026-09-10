from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, QueueToken, Patient, Doctor, Chair, Appointment, AuditLog
from firebase_service import sync_queue_token_to_firestore

queue_bp = Blueprint('queue', __name__)

@queue_bp.route('/queue')
@login_required
def index():
    doctors = Doctor.query.all()
    chairs = Chair.query.all()
    patients = Patient.query.all()
    return render_template('queue.html', doctors=doctors, chairs=chairs, patients=patients)

@queue_bp.route('/api/queue')
@login_required
def get_queue():
    tokens = QueueToken.query.filter(QueueToken.status.in_(['Waiting', 'Serving'])).order_by(QueueToken.is_emergency.desc(), QueueToken.id.asc()).all()
    now_serving = [t.to_dict() for t in tokens if t.status == 'Serving']
    up_next = [t.to_dict() for t in tokens if t.status == 'Waiting']
    
    return jsonify({
        'now_serving': now_serving,
        'up_next': up_next,
        'all_tokens': [t.to_dict() for t in tokens]
    })

@queue_bp.route('/api/queue/add', methods=['POST'])
@login_required
def add_token():
    data = request.get_json()
    token_count = QueueToken.query.count() + 14
    
    token = QueueToken(
        appointment_id=data.get('appointment_id'),
        patient_id=int(data.get('patient_id')),
        token_number=f"Token #{str(token_count).zfill(3)}",
        doctor_id=int(data.get('doctor_id', 1)),
        chair_id=int(data.get('chair_id', 1)) if data.get('chair_id') else 1,
        procedure_name=data.get('procedure_name', 'Walk-in Consultation'),
        status='Waiting',
        is_emergency=bool(data.get('is_emergency', False)),
        estimated_wait_min=int(data.get('estimated_wait_min', 15))
    )
    db.session.add(token)
    db.session.commit()

    token_dict = token.to_dict()
    sync_queue_token_to_firestore(token_dict)

    return jsonify({'status': 'success', 'message': f'{token.token_number} generated', 'token': token_dict})

@queue_bp.route('/api/queue/<int:token_id>/action', methods=['POST'])
@login_required
def token_action(token_id):
    token = QueueToken.query.get_or_404(token_id)
    data = request.get_json()
    action = data.get('action') # call, start, complete, skip

    if action == 'call':
        token.status = 'Serving'
        token.called_at = datetime.utcnow()
        if token.chair:
            token.chair.status = 'Patient Waiting'
            token.chair.current_patient = token.patient.name if token.patient else 'Patient'
    elif action == 'start':
        token.status = 'Serving'
        if token.appointment:
            token.appointment.status = 'In Treatment'
        if token.chair:
            token.chair.status = 'In Treatment'
            token.chair.current_patient = token.patient.name if token.patient else 'Patient'
            token.chair.current_doctor = token.doctor.name if token.doctor else 'Doctor'
            token.chair.current_procedure = token.procedure_name
            token.chair.session_start_time = datetime.utcnow()
    elif action == 'complete':
        token.status = 'Completed'
        if token.appointment:
            token.appointment.status = 'Completed'
        if token.chair:
            token.chair.status = 'Cleaning'
            token.chair.current_patient = None
            token.chair.current_procedure = None
    elif action == 'skip':
        token.status = 'Skipped'
        if token.appointment:
            token.appointment.status = 'No-Show'

    db.session.commit()

    token_dict = token.to_dict()
    sync_queue_token_to_firestore(token_dict)

    # Log audit
    log = AuditLog(
        user_name=current_user.name,
        user_role=current_user.role,
        action=f"Queue token action '{action}' performed for {token.token_number}",
        module="Queue",
        ip_address=request.remote_addr or '127.0.0.1'
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'status': 'success', 'message': f'Token action {action} applied', 'token': token_dict})
