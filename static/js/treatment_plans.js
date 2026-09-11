/**
 * DentiFlow - Treatment Plans Script
 */

document.addEventListener('DOMContentLoaded', () => {
    initTreatmentPlanForm();
});

async function updatePlanStatus(planId, newStatus) {
    try {
        const res = await fetch(`/api/treatment-plans/${planId}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        const data = await res.json();
        if (data.status === 'success') {
            window.toast(`Treatment plan ${newStatus.toLowerCase()}!`, 'success');
            setTimeout(() => window.location.reload(), 700);
        } else {
            window.toast(data.message || 'Error updating plan status', 'danger');
        }
    } catch (err) {
        window.toast('Error communicating with server', 'danger');
    }
}
window.updatePlanStatus = updatePlanStatus;

async function convertPlanToInvoice(planId) {
    try {
        const res = await fetch(`/api/treatment-plans/${planId}/convert-to-invoice`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (data.status === 'success') {
            window.toast(`Invoice ${data.invoice.invoice_number} generated from treatment plan!`, 'success');
            setTimeout(() => {
                window.location.href = '/billing';
            }, 1000);
        } else {
            window.toast(data.message || 'Could not convert plan to invoice', 'danger');
        }
    } catch (err) {
        window.toast('Error creating invoice from plan', 'danger');
    }
}
window.convertPlanToInvoice = convertPlanToInvoice;

function initTreatmentPlanForm() {
    const form = document.getElementById('new-plan-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const payload = {
            patient_id: parseInt(formData.get('patient_id')),
            doctor_id: parseInt(formData.get('doctor_id') || 1),
            title: formData.get('title'),
            total_cost: parseFloat(formData.get('total_cost') || 0),
            discount_amount: parseFloat(formData.get('discount_amount') || 0),
            notes: formData.get('notes'),
            phases: [
                {
                    phase_number: 1,
                    title: 'Clinical Treatment Phase',
                    status: 'Pending',
                    estimated_duration_weeks: 2,
                    items: [
                        {
                            tooth_number: formData.get('tooth_number') || '16',
                            procedure_name: formData.get('procedure_name'),
                            unit_cost: parseFloat(formData.get('total_cost') || 0),
                            discount: parseFloat(formData.get('discount_amount') || 0)
                        }
                    ]
                }
            ]
        };

        try {
            const res = await fetch('/api/treatment-plans', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.status === 'success') {
                window.toast(`Treatment Plan ${data.plan.plan_number} created!`, 'success');
                form.reset();
                const modal = document.getElementById('modal-build-plan');
                if (modal) modal.hidden = true;
                setTimeout(() => window.location.reload(), 700);
            } else {
                window.toast(data.message || 'Error saving plan', 'danger');
            }
        } catch (err) {
            window.toast('Error saving treatment plan', 'danger');
        }
    });
}
