from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import (
    db, LabOrder, Equipment, ReferralDoctor, FeedbackNPS, Campaign,
    InsuranceClaim, Patient, Doctor, AuditLog
)
from security import admin_required, staff_required, log_audit_event

operations_bp = Blueprint('operations', __name__)

@operations_bp.route('/operations')
@login_required
@admin_required
def index():
    lab_orders = LabOrder.query.order_by(LabOrder.id.desc()).all()
    equipments = Equipment.query.all()
    referrals = ReferralDoctor.query.all()
    campaigns = Campaign.query.all()
    claims = InsuranceClaim.query.all()
    feedback = FeedbackNPS.query.order_by(FeedbackNPS.id.desc()).all()
    patients = Patient.query.order_by(Patient.name.asc()).all()
    doctors = Doctor.query.all()
    
    return render_template(
        'operations.html',
        lab_orders=lab_orders,
        equipments=equipments,
        referrals=referrals,
        campaigns=campaigns,
        claims=claims,
        feedback=feedback,
        patients=patients,
        doctors=doctors
    )

# 1. Dental Lab Orders Tracker
@operations_bp.route('/api/lab-orders', methods=['GET', 'POST'])
@operations_bp.route('/api/operations/lab-orders', methods=['GET', 'POST'])
@login_required
@staff_required
def api_lab_orders():
    if request.method == 'POST':
        data = request.get_json()
        count = LabOrder.query.count() + 108
        order_no = f"LAB-2026-{count}"

        due_d = date.today() + timedelta(days=int(data.get('delivery_days', 4)))
        order = LabOrder(
            order_number=order_no,
            patient_id=int(data.get('patient_id')),
            doctor_id=int(data.get('doctor_id', 1)),
            lab_name=data.get('lab_name', 'DentCraft Precision Digital Lab'),
            restoration_type=data.get('restoration_type', 'Zirconia Crown'),
            tooth_numbers=data.get('tooth_numbers', '16'),
            shade=data.get('shade', 'A2'),
            stage='Sent to Lab',
            due_date=due_d,
            cost=float(data.get('cost', 2500.0)),
            notes=data.get('notes')
        )
        db.session.add(order)
        db.session.commit()

        # Log audit
        log_audit_event(
            action=f"Sent Lab Order {order.order_number} ({order.restoration_type}) to {order.lab_name}",
            module="Lab Operations",
            details=f"Order Number: {order.order_number}, Lab: {order.lab_name}, Cost: {order.cost}"
        )

        return jsonify({'status': 'success', 'message': 'Lab order placed', 'order': order.to_dict()}), 201

    orders = LabOrder.query.order_by(LabOrder.id.desc()).all()
    return jsonify({'orders': [o.to_dict() for o in orders]})

@operations_bp.route('/api/lab-orders/<int:order_id>/stage', methods=['POST'])
@login_required
@staff_required
def update_lab_stage(order_id):
    order = LabOrder.query.get_or_404(order_id)
    data = request.get_json()
    new_stage = data.get('stage') # Prescription, Sent to Lab, In Production, Quality Check, Ready, Delivered
    order.stage = new_stage
    db.session.commit()
    log_audit_event(
        action=f"Updated Lab Order #{order.id} stage to '{new_stage}'",
        module="Lab Operations"
    )
    return jsonify({'status': 'success', 'message': f'Lab order stage updated to {new_stage}', 'order': order.to_dict()})

# 2. Equipment Maintenance Log
@operations_bp.route('/api/equipment/<int:equipment_id>/service', methods=['POST'])
@login_required
@admin_required
def service_equipment(equipment_id):
    eq = Equipment.query.get_or_404(equipment_id)
    today = date.today()
    eq.last_service_date = today
    eq.next_service_due = today + timedelta(days=90)
    eq.status = 'Operational'
    db.session.commit()

    # Log audit
    log_audit_event(
        action=f"Logged routine service for equipment '{eq.name}'",
        module="Equipment",
        details=f"Equipment: {eq.name}, Next Service Due: {eq.next_service_due}"
    )

    return jsonify({'status': 'success', 'message': f'Service logged for {eq.name}', 'equipment': eq.to_dict()})

# 3. Marketing Campaign Launcher Simulator
@operations_bp.route('/api/campaigns/<int:campaign_id>/launch', methods=['POST'])
@login_required
@admin_required
def launch_campaign(campaign_id):
    camp = Campaign.query.get_or_404(campaign_id)
    camp.status = 'Active'
    camp.sent_count = camp.total_targeted
    camp.engaged_count = int(camp.total_targeted * 0.75)
    camp.appointments_booked = int(camp.total_targeted * 0.30)
    db.session.commit()

    # Log audit
    log_audit_event(
        action=f"Launched Marketing Campaign '{camp.title}' via {camp.channels}",
        module="Marketing",
        details=f"Campaign ID: {camp.id}, Sent: {camp.sent_count}"
    )

    return jsonify({
        'status': 'success',
        'message': f"Campaign '{camp.title}' launched! {camp.sent_count} WhatsApp messages dispatched.",
        'campaign': camp.to_dict()
    })

# 4. Patient Feedback & NPS
@operations_bp.route('/api/feedback', methods=['POST'])
@login_required
def submit_feedback():
    data = request.get_json()
    score = int(data.get('score', 10))
    category = 'Promoter' if score >= 9 else ('Passive' if score >= 7 else 'Detractor')
    
    fb = FeedbackNPS(
        patient_id=int(data.get('patient_id', 1)),
        doctor_id=int(data.get('doctor_id', 1)),
        score=score,
        category=category,
        comments=data.get('comments', 'Great experience'),
        root_cause=data.get('root_cause') if category == 'Detractor' else None
    )
    db.session.add(fb)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Feedback recorded', 'feedback': fb.to_dict()})
