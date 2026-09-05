from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import (
    db, Invoice, InvoiceItem, Payment, EMIPlan, PaymentInstallment,
    Patient, Doctor, Branch, AuditLog
)

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/billing')
@login_required
def index():
    invoices = Invoice.query.order_by(Invoice.id.desc()).all()
    patients = Patient.query.order_by(Patient.name.asc()).all()
    doctors = Doctor.query.all()
    return render_template('billing.html', invoices=invoices, patients=patients, doctors=doctors)

@billing_bp.route('/api/invoices', methods=['GET', 'POST'])
@login_required
def api_invoices():
    if request.method == 'POST':
        data = request.get_json()
        count = Invoice.query.count() + 1032
        inv_no = f"INV-2026-{count}"

        subtotal = float(data.get('subtotal', 0.0))
        discount_amount = float(data.get('discount_amount', 0.0))
        taxable = max(0.0, subtotal - discount_amount)
        tax_rate = float(data.get('tax_rate', 18.0))
        tax_amount = round(taxable * (tax_rate / 100.0), 2)
        total_amount = taxable + tax_amount

        invoice = Invoice(
            invoice_number=inv_no,
            patient_id=int(data.get('patient_id')),
            doctor_id=int(data.get('doctor_id', 1)),
            branch_id=int(data.get('branch_id', 1)),
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_amount=total_amount,
            paid_amount=0.0,
            due_amount=total_amount,
            status='Pending',
            payment_method=data.get('payment_method', 'UPI'),
            notes=data.get('notes'),
            due_date=date.today() + timedelta(days=14)
        )
        db.session.add(invoice)
        db.session.commit()

        # Add invoice items
        for itm in data.get('items', []):
            u_price = float(itm.get('unit_price', 0.0))
            disc = float(itm.get('discount', 0.0))
            qty = int(itm.get('quantity', 1))
            taxable_line = max(0.0, (u_price * qty) - disc)
            gst_line = round(taxable_line * 0.18, 2)
            
            inv_item = InvoiceItem(
                invoice_id=invoice.id,
                description=itm.get('description'),
                sac_code=itm.get('sac_code', '999312'),
                quantity=qty,
                unit_price=u_price,
                discount=disc,
                taxable_amount=taxable_line,
                gst_rate=18.0,
                total_amount=taxable_line + gst_line
            )
            db.session.add(inv_item)

        # Update patient outstanding
        patient = Patient.query.get(invoice.patient_id)
        if patient:
            patient.outstanding_balance += invoice.due_amount

        db.session.commit()

        # Log audit
        log = AuditLog(
            user_name=current_user.name,
            user_role=current_user.role,
            action=f"Created Invoice {invoice.invoice_number} (₹{invoice.total_amount:,.0f}) for {patient.name if patient else ''}",
            module="Billing",
            ip_address=request.remote_addr or '127.0.0.1'
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Invoice created successfully', 'invoice': invoice.to_dict()}), 201

    patient_id = request.args.get('patient_id')
    query = Invoice.query
    if patient_id:
        query = query.filter_by(patient_id=int(patient_id))
    invoices = query.order_by(Invoice.id.desc()).all()
    return jsonify({'invoices': [inv.to_dict() for inv in invoices]})

@billing_bp.route('/api/invoices/<int:invoice_id>')
@login_required
def get_invoice_detail(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return jsonify({'invoice': invoice.to_dict()})

@billing_bp.route('/api/payments', methods=['POST'])
@login_required
def record_payment():
    data = request.get_json()
    invoice_id = int(data.get('invoice_id'))
    invoice = Invoice.query.get_or_404(invoice_id)
    
    amount = float(data.get('amount', 0.0))
    payment_method = data.get('payment_method', 'UPI')
    txn_id = data.get('transaction_id') or f"TXN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    count = Payment.query.count() + 906
    rcp_no = f"RCP-2026-{count}"

    payment = Payment(
        receipt_number=rcp_no,
        invoice_id=invoice.id,
        patient_id=invoice.patient_id,
        amount=amount,
        payment_method=payment_method,
        transaction_id=txn_id,
        notes=data.get('notes'),
        status='Success'
    )
    db.session.add(payment)

    # Update invoice paid and due amounts
    invoice.paid_amount += amount
    invoice.due_amount = max(0.0, invoice.total_amount - invoice.paid_amount)
    
    if invoice.due_amount <= 0:
        invoice.status = 'Paid'
    else:
        invoice.status = 'Partial'

    # Update patient balances
    patient = Patient.query.get(invoice.patient_id)
    if patient:
        patient.outstanding_balance = max(0.0, patient.outstanding_balance - amount)
        patient.total_spent += amount

    # Check if EMI plan exists and record installment paid
    if invoice.emi_plan:
        pending_inst = PaymentInstallment.query.filter_by(emi_plan_id=invoice.emi_plan.id, status='Pending').first()
        if pending_inst:
            pending_inst.status = 'Paid'
            pending_inst.paid_date = datetime.utcnow()
            pending_inst.payment_method = payment_method

    db.session.commit()

    # Log audit
    log = AuditLog(
        user_name=current_user.name,
        user_role=current_user.role,
        action=f"Recorded {payment_method} Payment of ₹{amount:,.0f} ({payment.receipt_number}) for Invoice {invoice.invoice_number}",
        module="Billing",
        ip_address=request.remote_addr or '127.0.0.1'
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f'Payment of ₹{amount:,.0f} recorded successfully',
        'payment': payment.to_dict(),
        'invoice': invoice.to_dict()
    })

# Printable view for Invoice
@billing_bp.route('/invoices/<int:invoice_id>/print')
@login_required
def print_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template('print_invoice.html', invoice=invoice)

# Printable view for Payment Receipt
@billing_bp.route('/receipts/<int:payment_id>/print')
@login_required
def print_receipt(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    return render_template('print_receipt.html', payment=payment)
