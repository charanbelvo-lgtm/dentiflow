from datetime import datetime, date
from flask import Blueprint, render_template, request, jsonify
from models import db, Appointment, Patient, Doctor, TreatmentMaster, QueueToken, Branch

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
        count = Patient.query.count() + 1
        patient_id_code = f"DF-2026-{str(count).zfill(3)}"
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
    apt_count = Appointment.query.count() + 1080
    apt_date = datetime.strptime(apt_date_str, '%Y-%m-%d').date() if apt_date_str else date.today()

    appointment = Appointment(
        appointment_number=f"APT-{apt_count}",
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

    return jsonify({
        'status': 'success',
        'message': 'Your appointment request has been confirmed! An instant WhatsApp confirmation has been dispatched.',
        'appointment_number': appointment.appointment_number,
        'patient_name': patient.name,
        'doctor_name': appointment.doctor.name if appointment.doctor else 'Dr. Sharma',
        'date': appointment.appointment_date.strftime('%d %b %Y'),
        'time': appointment.start_time
    })
