from datetime import datetime, date
from flask import Blueprint, render_template, request, jsonify
from models import db, Appointment, Patient, Doctor, TreatmentMaster, QueueToken, Branch
from firebase_service import sync_patient_to_firestore

public_bp = Blueprint('public', __name__)

@public_bp.route('/book')
def booking_page():
    doctors = Doctor.query.all()
    treatments = TreatmentMaster.query.all()
    branches = Branch.query.all()
    return render_template('booking.html', doctors=doctors, treatments=treatments, branches=branches)

@public_bp.route('/portal')
def patient_portal():
    patient = Patient.query.first() # Default demo patient (Rahul Mehta)
    doctors = Doctor.query.all()
    return render_template('patient_portal.html', patient=patient, doctors=doctors)

@public_bp.route('/api/public/book', methods=['POST'])
def public_book():
    data = request.get_json()
    name = data.get('name')
    phone = data.get('phone')
    email = data.get('email')
    doctor_id = int(data.get('doctor_id', 1))
    treatment_name = data.get('treatment_name', 'General Consultation')
    apt_date_str = data.get('appointment_date')
    start_time = data.get('start_time', '10:00 AM')

    # Find or create patient
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
            email=email,
            age=int(data.get('age', 28)),
            gender=data.get('gender', 'Male'),
            primary_doctor_id=doctor_id,
            branch_id=1
        )
        db.session.add(patient)
        db.session.commit()

    # Create Appointment
    last_apt = Appointment.query.order_by(Appointment.id.desc()).first()
    next_apt_num = (last_apt.id + 1081) if last_apt else 1081
    apt_no_str = f"APT-{next_apt_num}"
    while Appointment.query.filter_by(appointment_number=apt_no_str).first():
        next_apt_num += 1
        apt_no_str = f"APT-{next_apt_num}"

    apt_date = datetime.strptime(apt_date_str, '%Y-%m-%d').date() if apt_date_str else date.today()

    appointment = Appointment(
        appointment_number=apt_no_str,
        patient_id=patient.id,
        doctor_id=doctor_id,
        chair_id=1,
        branch_id=1,
        appointment_date=apt_date,
        start_time=start_time,
        duration_minutes=30,
        procedure_name=treatment_name,
        status='Confirmed',
        booking_source='Online Portal',
        deposit_amount=0.0,
        notes=f"Self-booked via DentiFlow Online Portal by patient."
    )
    db.session.add(appointment)
    db.session.commit()

    # Sync patient to Firestore
    sync_patient_to_firestore(patient.to_dict())

    return jsonify({
        'status': 'success',
        'message': 'Your appointment request has been confirmed! An instant WhatsApp confirmation has been dispatched.',
        'appointment_number': appointment.appointment_number,
        'patient_name': patient.name,
        'doctor_name': appointment.doctor.name if appointment.doctor else 'Dr. Sharma',
        'date': appointment.appointment_date.strftime('%d %b %Y'),
        'time': appointment.start_time
    })
