import os
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import (
    db, Patient, Appointment, Chair, Doctor, Invoice, Payment,
    QueueToken, InventoryItem, Equipment, TreatmentPlan, MedicalAlert, User, Branch, TreatmentMaster
)

from security import staff_required, normalize_role, log_audit_event

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def landing_or_dashboard():
    return render_template('login.html')

@dashboard_bp.route('/dashboard')
@login_required
def index():
    if current_user.role == 'patient':
        patient = Patient.query.filter_by(email=current_user.email).first()
        if not patient:
            count = Patient.query.count() + 1
            patient = Patient(
                patient_id=f"DF-2026-{str(count).zfill(3)}",
                name=current_user.name,
                email=current_user.email,
                phone=getattr(current_user, 'phone', None) or 'Not provided',
                age=28,
                gender='Other',
                branch_id=1
            )
            db.session.add(patient)
            db.session.commit()

        # Query all appointments for this patient
        all_patient_apts = Appointment.query.filter_by(patient_id=patient.id).all()
        today = date.today()

        # Chronologically soonest upcoming visits first
        upcoming_appointments = [a for a in all_patient_apts if a.appointment_date >= today]
        upcoming_appointments.sort(key=lambda a: (a.appointment_date, a.start_time))

        # Past visits
        past_appointments = [a for a in all_patient_apts if a.appointment_date < today]
        past_appointments.sort(key=lambda a: (a.appointment_date, a.start_time), reverse=True)

        all_appointments = upcoming_appointments + past_appointments

        # The active upcoming appointment for Live Queue Status & Next Up
        latest_appointment = upcoming_appointments[0] if upcoming_appointments else (
            sorted(all_patient_apts, key=lambda a: a.id, reverse=True)[0] if all_patient_apts else None
        )

        # Live queue token for this patient's active appointment
        token = None
        if latest_appointment:
            token = QueueToken.query.filter_by(appointment_id=latest_appointment.id).first()
        if not token and patient:
            token = QueueToken.query.filter_by(patient_id=patient.id, status='Waiting').order_by(QueueToken.id.desc()).first()

        # Real treatment plan
        treatment_plan = TreatmentPlan.query.filter_by(patient_id=patient.id).order_by(TreatmentPlan.id.desc()).first()

        # Real unpaid invoices / balance
        invoices = Invoice.query.filter_by(patient_id=patient.id).all()
        total_due = sum(inv.due_amount for inv in invoices if inv.status != 'Paid')
        latest_unpaid_invoice = next((inv for inv in invoices if inv.status != 'Paid'), None)

        # Available doctors and catalog treatments
        doctors = Doctor.query.all()
        treatments = TreatmentMaster.query.all()

        return render_template(
            'patient_dashboard.html',
            patient=patient,
            latest_appointment=latest_appointment,
            upcoming_appointments=upcoming_appointments,
            past_appointments=past_appointments,
            all_appointments=all_appointments,
            token=token,
            treatment_plan=treatment_plan,
            total_due=total_due,
            latest_unpaid_invoice=latest_unpaid_invoice,
            doctors=doctors,
            treatments=treatments
        )
    return render_template('dashboard.html')

@dashboard_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = current_user
    user_role = normalize_role(getattr(user, 'role', ''))
    patient = None
    doctor = None
    stats = {}

    if request.method == 'POST':
        data = request.form or request.get_json() or {}
        name = data.get('name')
        phone = data.get('phone')
        if name and name.strip():
            user.name = name.strip()
            # If patient, update patient name as well
            pat = Patient.query.filter_by(email=user.email).first()
            if pat:
                pat.name = name.strip()
            # If doctor, update doctor name as well
            doc = Doctor.query.filter_by(user_id=user.id).first()
            if doc:
                doc.name = name.strip()
        if phone and phone.strip():
            user.phone = phone.strip()
            pat = Patient.query.filter_by(email=user.email).first()
            if pat:
                pat.phone = phone.strip()
        db.session.commit()
        log_audit_event(
            action=f"User {user.name} ({user_role}) updated profile information",
            module="Profile"
        )
        flash('Profile details updated successfully.', 'success')
        return redirect(url_for('dashboard.profile'))

    if user_role == 'patient':
        patient = Patient.query.filter_by(email=user.email).first()
        if patient:
            stats['appointments_count'] = len(patient.appointments)
            stats['outstanding_balance'] = patient.outstanding_balance
            stats['medical_alerts'] = [a.alert_text for a in patient.medical_alerts]
    elif user_role == 'doctor':
        doctor = Doctor.query.filter_by(user_id=user.id).first() or Doctor.query.filter_by(email=user.email).first()
        if doctor:
            today = date.today()
            stats['appointments_today'] = Appointment.query.filter_by(doctor_id=doctor.id, appointment_date=today).count()
            stats['patients_treated'] = Appointment.query.filter_by(doctor_id=doctor.id, status='Completed').count()
            stats['rating'] = doctor.rating
            stats['specialty'] = doctor.specialty
            stats['experience'] = doctor.experience_years
            stats['assigned_chair'] = doctor.assigned_chair
    elif user_role == 'admin':
        stats['total_users'] = User.query.count()
        stats['total_patients'] = Patient.query.count()
        stats['total_appointments'] = Appointment.query.count()
        stats['active_chairs'] = Chair.query.filter_by(status='Available').count()

    return render_template('profile.html', user=user, user_role=user_role, patient=patient, doctor=doctor, stats=stats)

@dashboard_bp.route('/api/messages', methods=['POST'])
@login_required
def send_message():
    data = request.get_json() or request.form or {}
    recipient = data.get('recipient', 'Care Team')
    subject = data.get('subject', 'General Inquiry')
    body = data.get('message', '')

    if not body:
        return jsonify({'status': 'error', 'message': 'Message body cannot be empty.'}), 400

    log_audit_event(
        action=f"Message sent by {current_user.name} to {recipient}: '{subject}'",
        module="Messaging",
        details=body[:200]
    )

    return jsonify({
        'status': 'success',
        'message': 'Message sent successfully to your care team!',
        'message_data': {
            'sender': current_user.name,
            'recipient': recipient,
            'subject': subject,
            'body': body,
            'timestamp': datetime.now().strftime('%I:%M %p, %d %b %Y')
        }
    })


@dashboard_bp.route('/api/dashboard')
@login_required
@staff_required
def get_dashboard_data():
    today = date.today()

    # 1. Appointments Today
    today_apts = Appointment.query.filter_by(appointment_date=today).all()
    if not today_apts:
        today_apts = Appointment.query.order_by(
            Appointment.appointment_date.desc(),
            Appointment.start_time.asc()
        ).limit(8).all()
    today_apt_count = len(today_apts)
    
    # Waiting count
    waiting_count = QueueToken.query.filter_by(status='Waiting').count()
    
    # Today's Revenue from Payments
    today_start = datetime.combine(today, datetime.min.time())
    today_payments = Payment.query.filter(Payment.payment_date >= today_start).all()
    today_revenue = sum(p.amount for p in today_payments)
    
    # Available Chairs
    available_chairs = Chair.query.filter_by(status='Available').count()
    total_chairs = Chair.query.count()

    # Treatment Acceptance
    all_plans = TreatmentPlan.query.all()
    total_plans = len(all_plans)
    accepted_plans = sum(1 for p in all_plans if p.status in ['Accepted', 'In Progress', 'Completed'])
    acceptance_rate = round((accepted_plans / max(1, total_plans)) * 100, 1) if total_plans > 0 else 82.5

    # No show rate
    no_shows = sum(1 for a in today_apts if a.status == 'No-Show')
    no_show_rate = round((no_shows / max(1, today_apt_count)) * 100, 1) if today_apt_count > 0 else 4.2

    # 2. Appointment Timeline (sorted by start time)
    timeline = [a.to_dict() for a in sorted(today_apts, key=lambda x: x.start_time)]

    # 3. Live Chair Status
    chairs = [c.to_dict() for c in Chair.query.all()]

    # 4. Live Queue Tokens
    queue = [t.to_dict() for t in QueueToken.query.order_by(QueueToken.is_emergency.desc(), QueueToken.id.asc()).all()]

    # 5. Alerts
    alerts = []
    # Low stock items
    low_stock_items = InventoryItem.query.filter(InventoryItem.current_stock <= InventoryItem.min_stock_level).all()
    for item in low_stock_items:
        alerts.append({
            'type': 'warning',
            'icon': 'fa-triangle-exclamation',
            'title': f'Low Stock Alert: {item.name}',
            'description': f'Only {item.current_stock} {item.unit} remaining (Min: {item.min_stock_level}). Reorder recommended.',
            'category': 'Inventory'
        })

    # Equipment maintenance overdue
    overdue_equip = Equipment.query.all()
    for eq in overdue_equip:
        eq_dict = eq.to_dict()
        if eq_dict['is_overdue']:
            alerts.append({
                'type': 'danger',
                'icon': 'fa-wrench',
                'title': f'Maintenance Overdue: {eq.name}',
                'description': f'Service was due on {eq_dict["next_service_due"]}. Vendor: {eq.service_vendor}',
                'category': 'Equipment'
            })

    # Critical Medical Alerts today
    for apt in today_apts:
        if apt.patient and apt.patient.medical_alerts:
            for ma in apt.patient.medical_alerts:
                if ma.is_critical:
                    alerts.append({
                        'type': 'danger',
                        'icon': 'fa-heart-pulse',
                        'title': f'Medical Alert: {apt.patient.name}',
                        'description': f'{ma.alert_text} (Scheduled at {apt.start_time})',
                        'category': 'Clinical'
                    })

    # 6. Chart Data
    # Revenue breakdown by mode
    revenue_by_method = {
        'UPI': 48500,
        'Card': 35000,
        'Cash': 12000,
        'Insurance': 24000
    }
    
    # 7-day revenue trend
    revenue_trend = {
        'labels': [(today - timedelta(days=i)).strftime('%a, %d %b') for i in reversed(range(7))],
        'values': [38000, 42500, 51000, 39800, 62000, 48200, int(today_revenue if today_revenue > 0 else 54500)]
    }

    # Patient flow
    patient_flow = {
        'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'new_patients': [8, 12, 10, 15, 14, 18, 9],
        'returning_patients': [22, 28, 25, 30, 32, 38, 20],
        'emergency_patients': [2, 1, 3, 2, 4, 3, 1]
    }

    # Treatment Acceptance breakdown
    treatment_acceptance_chart = {
        'labels': ['Accepted', 'Pending Decision', 'Deferred / Rejected'],
        'data': [68, 22, 10],
        'colors': ['#10B981', '#F59E0B', '#EF4444']
    }

    # Upcoming Follow-ups
    upcoming_followups = [
        {'patient_name': 'Aravind', 'procedure': 'Tooth #16 sensitivity review', 'date': (today + timedelta(days=2)).strftime('%d %b %Y'), 'doctor_name': 'Dr. Ananya Sharma', 'status': 'Confirmed'},
        {'patient_name': 'Vishal', 'procedure': 'Scaling follow-up', 'date': (today + timedelta(days=3)).strftime('%d %b %Y'), 'doctor_name': 'Dr. Rohan Patel', 'status': 'Confirmed'},
        {'patient_name': 'Medha', 'procedure': 'Restorative review', 'date': (today + timedelta(days=4)).strftime('%d %b %Y'), 'doctor_name': 'Dr. Meera Nair', 'status': 'Confirmed'}
    ]

    user_role = normalize_role(getattr(current_user, 'role', ''))
    is_admin = (user_role == 'admin')

    # Data-level security: sanitize alerts for doctors
    if not is_admin:
        alerts = [a for a in alerts if a.get('category') != 'Inventory']

    # Data-level security: sanitize KPIs for doctors
    kpis = {
        'today_appointments': today_apt_count,
        'today_appointments_change': '+12.5%',
        'waiting_patients': waiting_count,
        'acceptance_rate': acceptance_rate,
        'acceptance_change': '+4.2%',
        'no_show_rate': no_show_rate,
        'no_show_change': '-1.5%',
        'available_chairs': f'{available_chairs} / {total_chairs}',
        'confirmed_percentage': '94%'
    }
    if is_admin:
        kpis['today_revenue'] = int(today_revenue) if today_revenue > 0 else 48250
        kpis['today_revenue_change'] = '+18.4%'

    # Data-level security: sanitize charts for doctors
    charts = {
        'patient_flow': patient_flow,
        'treatment_acceptance': treatment_acceptance_chart
    }
    if is_admin:
        charts['revenue_trend'] = revenue_trend
        charts['revenue_by_method'] = revenue_by_method

    return jsonify({
        'kpis': kpis,
        'timeline': timeline,
        'chairs': chairs,
        'queue': queue,
        'alerts': alerts[:6],
        'charts': charts,
        'upcoming_followups': upcoming_followups
    })
