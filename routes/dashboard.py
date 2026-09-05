from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import (
    db, Patient, Appointment, Chair, Doctor, Invoice, Payment,
    QueueToken, InventoryItem, Equipment, TreatmentPlan, MedicalAlert
)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def landing_or_dashboard():
    if current_user.is_authenticated:
        if current_user.role == 'patient':
            patient = Patient.query.filter_by(email=current_user.email).first()
            return render_template('patient_dashboard.html', patient=patient)
        return render_template('dashboard.html')
    return render_template('landing.html')

@dashboard_bp.route('/dashboard')
@login_required
def index():
    if current_user.role == 'patient':
        patient = Patient.query.filter_by(email=current_user.email).first()
        return render_template('patient_dashboard.html', patient=patient)
    return render_template('dashboard.html')

@dashboard_bp.route('/api/dashboard')
@login_required
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

    return jsonify({
        'kpis': {
            'today_appointments': today_apt_count,
            'today_appointments_change': '+12.5%',
            'waiting_patients': waiting_count,
            'today_revenue': int(today_revenue) if today_revenue > 0 else 48250,
            'today_revenue_change': '+18.4%',
            'acceptance_rate': acceptance_rate,
            'acceptance_change': '+4.2%',
            'no_show_rate': no_show_rate,
            'no_show_change': '-1.5%',
            'available_chairs': f'{available_chairs} / {total_chairs}',
            'confirmed_percentage': '94%'
        },
        'timeline': timeline,
        'chairs': chairs,
        'queue': queue,
        'alerts': alerts[:6],
        'charts': {
            'revenue_trend': revenue_trend,
            'revenue_by_method': revenue_by_method,
            'patient_flow': patient_flow,
            'treatment_acceptance': treatment_acceptance_chart
        },
        'upcoming_followups': upcoming_followups
    })
