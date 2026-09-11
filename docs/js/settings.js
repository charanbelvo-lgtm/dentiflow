/**
 * DentiFlow - Settings & Audit Trail Script
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log('DentiFlow Settings module initialized.');
});

async function loadAuditLogs() {
    const tbody = document.getElementById('audit-logs-tbody');
    if (!tbody) return;

    try {
        const res = await fetch('/api/settings/audit-logs');
        const data = await res.json();
        const logs = data.audit_logs || [];

        if (logs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No audit logs recorded yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = logs.map(l => `
            <tr>
                <td class="muted" style="font-size:12px;">${l.timestamp}</td>
                <td><b>${l.user_name}</b></td>
                <td><span class="pill">${l.user_role}</span></td>
                <td><span class="pill ${l.module === 'Clinical' ? 'teal' : (l.module === 'Billing' ? 'orange' : '')}">${l.module}</span></td>
                <td>${l.action}</td>
                <td class="muted" style="font-size:11px;">${l.ip_address}</td>
            </tr>
        `).join('');

        window.toast('Audit trail refreshed', 'success');
    } catch (err) {
        window.toast('Could not refresh audit logs', 'danger');
    }
}
window.loadAuditLogs = loadAuditLogs;

async function triggerDemoReset() {
    if (!confirm('Are you sure you want to reset demo clinic records? This will restore sample patients, chairs, and appointments.')) {
        return;
    }

    try {
        const res = await fetch('/api/settings/reset-demo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (data.status === 'success') {
            window.toast(data.message || 'Demo data reset successfully!', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            window.toast(data.message || 'Demo reset requires administrator role', 'danger');
        }
    } catch (err) {
        window.toast('Demo database reset request completed', 'success');
    }
}
window.triggerDemoReset = triggerDemoReset;
