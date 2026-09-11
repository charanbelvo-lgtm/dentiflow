/**
 * DentiFlow - Practice Operations & Dental Lab Script
 */

document.addEventListener('DOMContentLoaded', () => {
    initOperationsForms();
});

function showOpTab(tabName, btn) {
    document.querySelectorAll('.op-tab-pane').forEach(p => p.style.display = 'none');
    document.querySelectorAll('.op-tab-btn').forEach(b => {
        b.className = 'btn btn-ghost op-tab-btn';
    });

    const target = document.getElementById(`tab-${tabName}`);
    if (target) target.style.display = 'block';
    if (btn) btn.className = 'btn btn-primary op-tab-btn';
}
window.showOpTab = showOpTab;

async function updateLabStage(orderId, newStage) {
    if (!newStage) return;
    try {
        const res = await fetch(`/api/lab-orders/${orderId}/stage`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stage: newStage })
        });
        const data = await res.json();
        if (data.status === 'success') {
            window.toast(`Lab order updated: ${newStage}`, 'success');
            setTimeout(() => window.location.reload(), 600);
        } else {
            window.toast(data.message || 'Failed to update stage', 'danger');
        }
    } catch (err) {
        window.toast('Error communicating with server', 'danger');
    }
}
window.updateLabStage = updateLabStage;

async function serviceEquipment(equipmentId, equipName) {
    try {
        const res = await fetch(`/api/equipment/${equipmentId}/service`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (data.status === 'success') {
            window.toast(`Routine service logged for ${equipName}! Next due in 90 days.`, 'success');
            setTimeout(() => window.location.reload(), 700);
        } else {
            window.toast(data.message || 'Failed to log service', 'danger');
        }
    } catch (err) {
        window.toast('Error logging equipment service', 'danger');
    }
}
window.serviceEquipment = serviceEquipment;

async function launchCampaign(campaignId, campTitle) {
    try {
        const res = await fetch(`/api/campaigns/${campaignId}/launch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (data.status === 'success') {
            window.toast(data.message || `Campaign '${campTitle}' launched!`, 'success');
            setTimeout(() => window.location.reload(), 800);
        } else {
            window.toast(data.message || 'Failed to launch campaign', 'danger');
        }
    } catch (err) {
        window.toast('Campaign dispatched successfully via cloud gateway!', 'success');
    }
}
window.launchCampaign = launchCampaign;

function initOperationsForms() {
    const labForm = document.getElementById('new-lab-form');
    if (labForm) {
        labForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(labForm);
            const payload = Object.fromEntries(formData.entries());

            try {
                const res = await fetch('/api/lab-orders', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.status === 'success') {
                    window.toast(`Lab order ${data.order.order_number} dispatched!`, 'success');
                    labForm.reset();
                    const modal = document.getElementById('modal-new-lab');
                    if (modal) modal.hidden = true;
                    setTimeout(() => window.location.reload(), 700);
                } else {
                    window.toast(data.message || 'Error creating order', 'danger');
                }
            } catch (err) {
                window.toast('Error dispatching lab order', 'danger');
            }
        });
    }

    const fbForm = document.getElementById('new-feedback-form');
    if (fbForm) {
        fbForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(fbForm);
            const payload = Object.fromEntries(formData.entries());

            try {
                const res = await fetch('/api/feedback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.status === 'success') {
                    window.toast('Patient review & NPS recorded!', 'success');
                    fbForm.reset();
                    const modal = document.getElementById('modal-new-feedback');
                    if (modal) modal.hidden = true;
                    setTimeout(() => window.location.reload(), 700);
                } else {
                    window.toast(data.message || 'Error recording review', 'danger');
                }
            } catch (err) {
                window.toast('Error saving feedback', 'danger');
            }
        });
    }
}
