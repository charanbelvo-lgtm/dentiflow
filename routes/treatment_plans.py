from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import (
    db, TreatmentPlan, TreatmentPlanPhase, TreatmentPlanItem,
    Patient, Doctor, Invoice, InvoiceItem, AuditLog
)

treatment_plans_bp = Blueprint('treatment_plans', __name__)

@treatment_plans_bp.route('/treatment-plans')
@login_required
def index():
    plans = TreatmentPlan.query.order_by(TreatmentPlan.id.desc()).all()
    patients = Patient.query.order_by(Patient.name.asc()).all()
    doctors = Doctor.query.all()
    return render_template('treatment_plans.html', plans=plans, patients=patients, doctors=doctors)

@treatment_plans_bp.route('/api/treatment-plans', methods=['GET', 'POST'])
@login_required
def api_treatment_plans():
    if request.method == 'POST':
        data = request.get_json()
        count = TreatmentPlan.query.count() + 43
        plan_no = f"TP-2026-{str(count).zfill(3)}"

        total_cost = float(data.get('total_cost', 0.0))
        discount_amount = float(data.get('discount_amount', 0.0))
        net_cost = max(0.0, total_cost - discount_amount)

        plan = TreatmentPlan(
            plan_number=plan_no,
            patient_id=int(data.get('patient_id')),
            doctor_id=int(data.get('doctor_id', 1)),
            title=data.get('title', 'Comprehensive Treatment Plan'),
            status=data.get('status', 'Proposed'),
            total_cost=total_cost,
            discount_amount=discount_amount,
            net_cost=net_cost,
            accepted_amount=float(data.get('accepted_amount', 0.0)),
            notes=data.get('notes')
        )
        db.session.add(plan)
        db.session.commit()

        # Phases
        phases_data = data.get('phases', [])
        for p_idx, phase_item in enumerate(phases_data, 1):
            phase = TreatmentPlanPhase(
                plan_id=plan.id,
                phase_number=p_idx,
                title=phase_item.get('title', f'Phase {p_idx}'),
                status=phase_item.get('status', 'Pending'),
                estimated_duration_weeks=int(phase_item.get('estimated_duration_weeks', 2))
            )
            db.session.add(phase)
            db.session.commit()

            # Items inside phase
            for itm in phase_item.get('items', []):
                u_cost = float(itm.get('unit_cost', 0.0))
                disc = float(itm.get('discount', 0.0))
                n_cost = max(0.0, u_cost - disc)
                plan_item = TreatmentPlanItem(
                    phase_id=phase.id,
                    tooth_number=itm.get('tooth_number', 'General'),
                    procedure_name=itm.get('procedure_name'),
                    unit_cost=u_cost,
                    discount=disc,
                    net_cost=n_cost,
                    status='Pending'
                )
                db.session.add(plan_item)

        db.session.commit()

        # Log audit
        patient = Patient.query.get(plan.patient_id)
        log = AuditLog(
            user_name=current_user.name,
            user_role=current_user.role,
            action=f"Created Treatment Plan {plan.plan_number} (₹{plan.net_cost:,.0f}) for {patient.name if patient else ''}",
            module="Clinical",
            ip_address=request.remote_addr or '127.0.0.1'
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Treatment plan saved', 'plan': plan.to_dict()}), 201

    patient_id = request.args.get('patient_id')
    query = TreatmentPlan.query
    if patient_id:
        query = query.filter_by(patient_id=int(patient_id))
    plans = query.order_by(TreatmentPlan.id.desc()).all()
    return jsonify({'plans': [p.to_dict() for p in plans]})

@treatment_plans_bp.route('/api/treatment-plans/<int:plan_id>/status', methods=['POST'])
@login_required
def update_plan_status(plan_id):
    plan = TreatmentPlan.query.get_or_404(plan_id)
    data = request.get_json()
    new_status = data.get('status') # Proposed, Accepted, In Progress, Completed, Rejected
    plan.status = new_status
    if new_status == 'Accepted':
        plan.accepted_amount = plan.net_cost
    db.session.commit()
    return jsonify({'status': 'success', 'message': f'Plan marked as {new_status}', 'plan': plan.to_dict()})

@treatment_plans_bp.route('/api/treatment-plans/<int:plan_id>/convert-to-invoice', methods=['POST'])
@login_required
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
