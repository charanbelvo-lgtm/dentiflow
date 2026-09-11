// DentiFlow Inventory Management
window.adjustStock = async function(itemId, changeType, qty, itemName) {
    try {
        const res = await fetch(`/api/inventory/${itemId}/adjust`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                change_type: changeType,
                quantity: qty,
                reason: changeType === 'Add' ? 'Manual Restock batch' : 'Routine clinical usage'
            })
        });
        const data = await res.json();
        if (res.ok) {
            window.toast && window.toast(`${itemName}: ${changeType}ed ${qty} units`, 'success');
            setTimeout(() => window.location.reload(), 500);
        } else {
            window.toast && window.toast(data.message || 'Stock adjustment failed', 'error');
        }
    } catch (e) {
        console.error(e);
        window.toast && window.toast('Network error updating stock', 'error');
    }
};

document.addEventListener('DOMContentLoaded', () => {
    const itemForm = document.getElementById('new-item-form');
    if (itemForm) {
        itemForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(itemForm);
            const payload = {
                name: formData.get('name'),
                category: formData.get('category'),
                unit: formData.get('unit'),
                current_stock: parseInt(formData.get('current_stock') || '0', 10),
                min_stock_level: parseInt(formData.get('min_stock_level') || '5', 10),
                unit_price: parseFloat(formData.get('unit_price') || '0'),
                supplier_name: formData.get('supplier_name')
            };

            try {
                const res = await fetch('/api/inventory', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok) {
                    window.toast && window.toast('Item added to catalog!', 'success');
                    setTimeout(() => window.location.reload(), 600);
                } else {
                    window.toast && window.toast(data.message || 'Failed to add item', 'error');
                }
            } catch (err) {
                console.error(err);
                window.toast && window.toast('Server communication error', 'error');
            }
        });
    }
});
