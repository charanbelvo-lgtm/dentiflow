/**
 * DentiFlow - Billing & Invoicing Client Script
 */

document.addEventListener('DOMContentLoaded', () => {
    initBillingForms();
});

function initBillingForms() {
    // 1. Payment Form Handler
    const payForm = document.getElementById('payment-form');
    if (payForm) {
        payForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(payForm);
            const payload = {
                invoice_id: parseInt(formData.get('invoice_id')),
                amount: parseFloat(formData.get('amount') || 0),
                payment_method: formData.get('payment_method') || 'UPI',
                transaction_id: formData.get('transaction_id') || '',
                notes: formData.get('notes') || ''
            };

            if (payload.amount <= 0) {
                window.toast('Please enter a valid payment amount', 'danger');
                return;
            }

            try {
                const res = await fetch('/api/payments', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.status === 'success') {
                    window.toast(`Payment of ₹${payload.amount.toLocaleString('en-IN')} recorded! Receipt generated.`, 'success');
                    payForm.reset();
                    setTimeout(() => window.location.reload(), 900);
                } else {
                    window.toast(data.message || 'Payment recording failed', 'danger');
                }
            } catch (err) {
                window.toast('Error connecting to billing gateway', 'danger');
            }
        });
    }

    // 2. New Invoice Form Handler
    const invForm = document.getElementById('new-invoice-form');
    if (invForm) {
        invForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(invForm);
            const subtotal = parseFloat(formData.get('subtotal') || 0);
            const discount = parseFloat(formData.get('discount_amount') || 0);
            const taxRate = parseFloat(formData.get('tax_rate') || 18);

            const payload = {
                patient_id: parseInt(formData.get('patient_id')),
                doctor_id: parseInt(formData.get('doctor_id') || 1),
                subtotal: subtotal,
                discount_amount: discount,
                tax_rate: taxRate,
                payment_method: formData.get('payment_method') || 'UPI',
                notes: formData.get('notes') || '',
                items: [
                    {
                        description: formData.get('description') || 'Dental Clinical Procedure',
                        sac_code: formData.get('sac_code') || '999312',
                        quantity: 1,
                        unit_price: subtotal,
                        discount: discount
                    }
                ]
            };

            try {
                const res = await fetch('/api/invoices', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.status === 'success') {
                    window.toast(`Tax Invoice ${data.invoice.invoice_number} generated successfully!`, 'success');
                    invForm.reset();
                    const modal = document.getElementById('modal-create-invoice');
                    if (modal) modal.hidden = true;
                    setTimeout(() => window.location.reload(), 800);
                } else {
                    window.toast(data.message || 'Error generating invoice', 'danger');
                }
            } catch (err) {
                window.toast('Error communicating with invoice service', 'danger');
            }
        });
    }
}
