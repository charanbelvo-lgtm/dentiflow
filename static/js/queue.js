/**
 * DentiFlow - Queue & Token Management Script
 */

document.addEventListener('DOMContentLoaded', () => {
    loadQueueData();
    initTokenForm();
    initFirebaseRealtimeQueue();
});

async function initFirebaseRealtimeQueue() {
    // Wait briefly for Firebase client init
    setTimeout(async () => {
        if (window.DentiFlowFirebase && window.DentiFlowFirebase.isReady) {
            await window.DentiFlowFirebase.subscribeToQueue((realtimeData) => {
                renderNowServing(realtimeData.now_serving || []);
                renderUpNext(realtimeData.up_next || []);
                updateQueueCounts(realtimeData);
            });
        }
    }, 500);
}

function updateQueueCounts(data) {
    const servCount = document.getElementById('stat-serving-count');
    if (servCount) servCount.innerText = `${data.now_serving ? data.now_serving.length : 0} Active`;
    
    const waitCount = document.getElementById('stat-waiting-count');
    if (waitCount) waitCount.innerText = `${data.up_next ? data.up_next.length : 0} In Queue`;
    
    const waitBadge = document.getElementById('waiting-count-badge');
    if (waitBadge) waitBadge.innerText = `${data.up_next ? data.up_next.length : 0} Waiting`;
}

async function loadQueueData() {
    try {
        const res = await fetch('/api/queue');
        const data = await res.json();
        
        renderNowServing(data.now_serving || []);
        renderUpNext(data.up_next || []);
        updateQueueCounts(data);

        // Auto-seed active tokens into Firestore if Firebase is ready
        if (window.DentiFlowFirebase && window.DentiFlowFirebase.isReady && data.all_tokens) {
            data.all_tokens.forEach(tok => window.DentiFlowFirebase.syncQueueToken(tok));
        }
    } catch (err) {
        console.error('Error fetching queue:', err);
    }
}
window.loadQueueData = loadQueueData;

async function handleTokenAction(tokenId, action) {
    try {
        const res = await fetch(`/api/queue/${tokenId}/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action })
        });
        const data = await res.json();
        if (data.status === 'success') {
            if (action === 'call') playChime('bell');
            if (action === 'complete') playChime('success');
            showToast(data.message, 'success');

            // Sync to Firestore
            if (window.DentiFlowFirebase && window.DentiFlowFirebase.isReady && data.token) {
                window.DentiFlowFirebase.syncQueueToken(data.token);
            }

            loadQueueData();
        }
    } catch (err) {
        showToast('Error executing queue action', 'danger');
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
                showToast(`Token ${data.token.token_number} issued!`, 'success');

                // Sync to Firestore
                if (window.DentiFlowFirebase && window.DentiFlowFirebase.isReady && data.token) {
                    window.DentiFlowFirebase.syncQueueToken(data.token);
                }

                form.reset();
                const modalEl = document.getElementById('newQueueTokenModal');
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
                loadQueueData();
            }
        } catch (err) {
            showToast('Error issuing token', 'danger');
        }
    });
}
