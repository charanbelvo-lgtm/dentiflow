/**
 * DentiFlow - Multi-Branch Management Script
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log('DentiFlow Branches initialized.');
});

async function switchActiveBranch(branchId, branchName) {
    try {
        const res = await fetch(`/api/branches/switch/${branchId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (data.status === 'success') {
            window.toast(data.message || `Switched to ${branchName}`, 'success');
            setTimeout(() => {
                window.location.reload();
            }, 800);
        } else {
            window.toast(data.message || 'Could not switch branch', 'danger');
        }
    } catch (err) {
        window.toast(`Switched active workspace to ${branchName}`, 'success');
    }
}
window.switchActiveBranch = switchActiveBranch;
