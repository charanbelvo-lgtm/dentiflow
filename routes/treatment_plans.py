from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from models import (
    db, TreatmentPlan, TreatmentPlanPhase, TreatmentPlanItem,
    Patient, Doctor, Invoice, InvoiceItem, AuditLog
)
from security import clinical_required, staff_required, admin_required, log_audit_event, normalize_role

treatment_plans_bp = Blueprint('treatment_plans', __name__)

@treatment_plans_bp.route('/treatment-plans')
@login_required
@staff_required
def index():
    user_role = normalize_role(getattr(current_user, 'role', ''))
    if user_role == 'patient':
        patient = Patient.query.filter_by(email=current_user.email).first()
        plans = TreatmentPlan.query.filter_by(patient_id=patient.id).order_by(TreatmentPlan.id.desc()).all() if patient else []
        patients = [patient] if patient else []
    else:
        plans = TreatmentPlan.query.order_by(TreatmentPlan.id.desc()).all()
        patients = Patient.query.order_by(Patient.name.asc()).all()
    doctors = Doctor.query.all()
    return render_template('treatment_plans.html', plans=plans, patients=patients, doctors=doctors)

@treatment_plans_bp.route('/api/treatment-plans', methods=['GET', 'POST'])
@login_required
def api_treatment_plans():
    user_role = normalize_role(getattr(current_user, 'role', ''))


    if request.method == 'POST':
        if user_role not in {'admin', 'doctor'}:
            log_audit_event(
                action=f"ACCESS_DENIED: {current_user.name} ({user_role}) denied creating treatment plan",
                module="Authorization"
            )
            return jsonify({'status': 'error', 'message': 'Access forbidden: insufficient permissions.'}), 403
        data = request.get_json() or {}
        patient_id = data.get('patient_id')
        if not patient_id:
            return jsonify({'status': 'error', 'message': 'Please select a patient for the treatment plan.'}), 400
        try:
            patient_id = int(patient_id)
        except (ValueError, TypeError):
            return jsonify({'status': 'error', 'message': 'Invalid patient selected.'}), 400

        doctor_id = data.get('doctor_id')
        if not doctor_id and user_role == 'doctor':
            doc = Doctor.query.filter((Doctor.user_id == current_user.id) | (Doctor.email == current_user.email)).first()
            if doc:
                doctor_id = doc.id
        try:
            doctor_id = int(doctor_id) if doctor_id else 1
        except (ValueError, TypeError):
            doctor_id = 1

        count = TreatmentPlan.query.count() + 43
        plan_no = f"TP-2026-{str(count).zfill(3)}"

        try:
            total_cost = float(data.get('total_cost') or 0.0)
        except (ValueError, TypeError):
            total_cost = 0.0

        try:
            discount_amount = float(data.get('discount_amount') or 0.0)
        except (ValueError, TypeError):
            discount_amount = 0.0

        net_cost = max(0.0, total_cost - discount_amount)

        plan = TreatmentPlan(
            plan_number=plan_no,
            patient_id=patient_id,
            doctor_id=doctor_id,
            title=data.get('title') or 'Comprehensive Treatment Plan',
            status=data.get('status') or 'Proposed',
            total_cost=total_cost,
            discount_amount=discount_amount,
            net_cost=net_cost,
            accepted_amount=float(data.get('accepted_amount') or 0.0),
            notes=data.get('notes')
        )
        db.session.add(plan)
        db.session.commit()

        # Phases
        phases_data = data.get('phases', [])
        if not phases_data and (data.get('procedure_name') or data.get('title')):
            proc_name = data.get('procedure_name') or data.get('title') or 'General Dental Procedure'
            tooth_no = str(data.get('tooth_number') or 'General')
            try:
                duration = int(data.get('estimated_duration_weeks') or 2)
            except (ValueError, TypeError):
                duration = 2
            phases_data = [{
                'title': f"Phase 1: {proc_name}",
                'status': 'Pending',
                'estimated_duration_weeks': duration,
                'items': [{
                    'tooth_number': tooth_no,
                    'procedure_name': proc_name,
                    'unit_cost': total_cost,
                    'discount': discount_amount
                }]
            }]

        for p_idx, phase_item in enumerate(phases_data, 1):
            try:
                dur_weeks = int(phase_item.get('estimated_duration_weeks') or 2)
            except (ValueError, TypeError):
                dur_weeks = 2

            phase = TreatmentPlanPhase(
                plan_id=plan.id,
                phase_number=p_idx,
                title=phase_item.get('title', f'Phase {p_idx}'),
                status=phase_item.get('status', 'Pending'),
                estimated_duration_weeks=dur_weeks
            )
            db.session.add(phase)
            db.session.commit()

            # Items inside phase
            for itm in phase_item.get('items', []):
                try:
                    u_cost = float(itm.get('unit_cost') or 0.0)
                except (ValueError, TypeError):
                    u_cost = 0.0
                try:
                    disc = float(itm.get('discount') or 0.0)
                except (ValueError, TypeError):
                    disc = 0.0
                n_cost = max(0.0, u_cost - disc)
                plan_item = TreatmentPlanItem(
                    phase_id=phase.id,
                    tooth_number=str(itm.get('tooth_number') or 'General'),
                    procedure_name=itm.get('procedure_name', 'Dental Procedure'),
                    unit_cost=u_cost,
                    discount=disc,
                    net_cost=n_cost,
                    status='Pending'
                )
                db.session.add(plan_item)

        db.session.commit()

        # Log audit
        patient = Patient.query.get(plan.patient_id)
        log_audit_event(
            action=f"Created Treatment Plan {plan.plan_number} (₹{plan.net_cost:,.0f}) for {patient.name if patient else ''}",
            module="Clinical",
            details=f"Plan Number: {plan.plan_number}, Patient: {plan.patient_id}, Total: {plan.total_cost}"
        )

        return jsonify({'status': 'success', 'message': f'Treatment plan {plan.plan_number} created successfully!', 'plan': plan.to_dict()}), 201

    if user_role == 'patient':
        patient = Patient.query.filter_by(email=current_user.email).first()
        if not patient:
            return jsonify({'plans': []})
        plans = TreatmentPlan.query.filter_by(patient_id=patient.id).order_by(TreatmentPlan.id.desc()).all()
        return jsonify({'plans': [p.to_dict() for p in plans]})

    patient_id = request.args.get('patient_id')
    query = TreatmentPlan.query
    if patient_id:
        query = query.filter_by(patient_id=int(patient_id))
    plans = query.order_by(TreatmentPlan.id.desc()).all()
    return jsonify({'plans': [p.to_dict() for p in plans]})

@treatment_plans_bp.route('/api/treatment-plans/<int:plan_id>/status', methods=['POST'])
@login_required
@clinical_required
def update_plan_status(plan_id):
    plan = TreatmentPlan.query.get_or_404(plan_id)
    data = request.get_json()
    new_status = data.get('status') # Proposed, Accepted, In Progress, Completed, Rejected
    plan.status = new_status
    if new_status == 'Accepted':
        plan.accepted_amount = plan.net_cost
    db.session.commit()
    log_audit_event(
        action=f"Updated Treatment Plan #{plan.id} status to '{new_status}'",
        module="Clinical"
    )
    return jsonify({'status': 'success', 'message': f'Plan marked as {new_status}', 'plan': plan.to_dict()})

@treatment_plans_bp.route('/api/treatment-plans/<int:plan_id>/convert-to-invoice', methods=['POST'])
@login_required
@admin_required
def convert_to_invoice(plan_id):
    plan = TreatmentPlan.query.get_or_404(plan_id)
    
    count = Invoice.query.count() + 1031
    inv_no = f"INV-2026-{count}"
    
    # Calculate tax & total
    subtotal = plan.net_cost
    tax_rate = 18.0
    tax_amount = round(subtotal * (tax_rate / 100.0), 2)
    total_amount = subtotal + tax_amount

    invoice = Invoice(
        invoice_number=inv_no,
        patient_id=plan.patient_id,
        doctor_id=plan.doctor_id,
        branch_id=1,
        subtotal=subtotal,
        discount_amount=0.0,
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        total_amount=total_amount,
        paid_amount=0.0,
        due_amount=total_amount,
        status='Pending',
        payment_method='UPI',
        notes=f"Converted from Treatment Plan {plan.plan_number} ({plan.title})",
        due_date=date.today() + timedelta(days=14)
    )
    db.session.add(invoice)
    db.session.commit()

    # Add items from treatment plan
    for phase in plan.phases:
        for itm in phase.items:
            t_amt = itm.net_cost
            i_gst = round(t_amt * 0.18, 2)
            inv_item = InvoiceItem(
                invoice_id=invoice.id,
                description=f"{itm.procedure_name} (Tooth: {itm.tooth_number})",
                sac_code='999312',
                quantity=1,
                unit_price=itm.unit_cost,
                discount=itm.discount,
                taxable_amount=t_amt,
                gst_rate=18.0,
                total_amount=t_amt + i_gst
            )
            db.session.add(inv_item)

    plan.is_converted_to_invoice = True
    plan.status = 'In Progress'
    db.session.commit()

    # Log audit
    log = AuditLog(
        user_name=current_user.name,
        user_role=current_user.role,
        action=f"Converted Treatment Plan {plan.plan_number} to Invoice {invoice.invoice_number} (₹{invoice.total_amount:,.0f})",
        module="Billing",
        ip_address=request.remote_addr or '127.0.0.1'
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'status': 'success', 'message': f'Invoice {invoice.invoice_number} generated successfully', 'invoice': invoice.to_dict()})
