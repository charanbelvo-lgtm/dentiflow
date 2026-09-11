/**
 * DentiFlow - Live Queue & Token Management Script
 */

document.addEventListener('DOMContentLoaded', () => {
    loadQueueData();
    initTokenForm();
});

async function loadQueueData() {
    try {
        const res = await fetch('/api/queue');
        if (!res.ok) throw new Error('Network error');
        const data = await res.json();
        
        renderNowServing(data.now_serving || []);
        renderUpNext(data.up_next || []);
        updateQueueCounts(data);

        // Firestore sync if configured
        if (window.DentiFlowFirebase && window.DentiFlowFirebase.isReady && data.all_tokens) {
            data.all_tokens.forEach(tok => window.DentiFlowFirebase.syncQueueToken(tok));
        }
    } catch (err) {
        console.error('Error fetching queue:', err);
    }
}
window.loadQueueData = loadQueueData;

function updateQueueCounts(data) {
    const servCount = document.getElementById('stat-serving-count');
    if (servCount) servCount.innerText = `${(data.now_serving || []).length} Active`;
    
    const waitCount = document.getElementById('stat-waiting-count');
    if (waitCount) waitCount.innerText = `${(data.up_next || []).length} In Queue`;
    
    const waitBadge = document.getElementById('waiting-count-badge');
    if (waitBadge) waitBadge.innerText = `${(data.up_next || []).length} Waiting`;
}

function renderNowServing(tokens) {
    const container = document.getElementById('now-serving-container');
    if (!container || !tokens) return;

    if (tokens.length === 0) {
        // Leave chair cards as initialized or show idle
        return;
    }

    // Update matching operatory chair cards if present
    tokens.forEach(tok => {
        const chairCard = [...container.querySelectorAll('.card')].find(c => c.textContent.includes(`Chair 0${tok.chair_id}`) || c.textContent.includes(tok.chair_name || ''));
        if (chairCard) {
            const statusPill = chairCard.querySelector('.pill');
            if (statusPill) {
                statusPill.className = 'pill green';
                statusPill.innerText = 'In Treatment';
            }
        }
    });
}

function renderUpNext(tokens) {
    const tbody = document.getElementById('up-next-tbody');
    if (!tbody) return;

    if (tokens.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4 text-muted">
                    No patients currently waiting in reception. Queue is clear!
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = tokens.map(t => `
        <tr data-searchable>
            <td>
                <b>${t.token_number}</b>
                ${t.is_emergency ? '<span class="pill red" style="margin-left:6px;font-size:10px;">Emergency</span>' : ''}
            </td>
            <td>
                <strong>${t.patient_name || 'Patient'}</strong>
            </td>
            <td class="text-muted">${t.doctor_name || 'Attending Doctor'}</td>
            <td>${t.procedure_name || 'Consultation'}</td>
            <td>
                <span class="pill ${t.status === 'Serving' ? 'green' : 'orange'}">${t.status}</span>
            </td>
            <td class="text-muted">~${t.estimated_wait_min || 15} mins</td>
            <td>
                <div class="row" style="gap:6px;">
                    <button class="btn btn-soft" style="padding:4px 9px;font-size:12px;" onclick="handleTokenAction(${t.id}, 'call')">
                        Call to Chair
                    </button>
                    <button class="btn btn-teal" style="padding:4px 9px;font-size:12px;" onclick="handleTokenAction(${t.id}, 'start')">
                        Start
                    </button>
                    <button class="btn btn-ghost" style="padding:4px 9px;font-size:12px;" onclick="handleTokenAction(${t.id}, 'complete')">
                        Complete
                    </button>
                    <button class="btn btn-danger" style="padding:4px 9px;font-size:12px;" onclick="handleTokenAction(${t.id}, 'skip')">
                        Skip
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

async function handleTokenAction(tokenId, action) {
    try {
        const res = await fetch(`/api/queue/${tokenId}/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action })
        });
        const data = await res.json();
        if (data.status === 'success') {
            window.toast(data.message || 'Queue updated', 'success');

            if (window.DentiFlowFirebase && window.DentiFlowFirebase.isReady && data.token) {
                window.DentiFlowFirebase.syncQueueToken(data.token);
            }

            loadQueueData();
        } else {
            window.toast(data.message || 'Error updating queue', 'danger');
        }
    } catch (err) {
        window.toast('Error executing queue action', 'danger');
    }
}
window.handleTokenAction = handleTokenAction;

function initTokenForm() {
    const form = document.getElementById('new-token-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const payload = Object.fromEntries(formData.entries());
        payload.is_emergency = form.is_emergency ? form.is_emergency.checked : false;

        try {
            const res = await fetch('/api/queue/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.status === 'success') {
                window.toast(`Token ${data.token.token_number} issued successfully!`, 'success');

                if (window.DentiFlowFirebase && window.DentiFlowFirebase.isReady && data.token) {
                    window.DentiFlowFirebase.syncQueueToken(data.token);
                }

                form.reset();
                const modal = document.getElementById('modal-new-token');
                if (modal) modal.hidden = true;
                loadQueueData();
            } else {
                window.toast(data.message || 'Could not issue token', 'danger');
            }
        } catch (err) {
            window.toast('Error issuing token', 'danger');
        }
    });
}
