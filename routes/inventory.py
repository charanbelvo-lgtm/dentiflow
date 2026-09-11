from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import (
    db, InventoryItem, Supplier, PurchaseOrder, InventoryLog, AuditLog
)

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory')
@login_required
def index():
    items = InventoryItem.query.order_by(InventoryItem.name.asc()).all()
    suppliers = Supplier.query.all()
    categories = ['Dental Materials', 'Consumables', 'Lab Materials', 'Medicines', 'Equipment']
    return render_template('inventory.html', items=items, suppliers=suppliers, categories=categories)

@inventory_bp.route('/api/inventory', methods=['GET', 'POST'])
@login_required
def api_inventory():
    if request.method == 'POST':
        data = request.get_json()
        count = InventoryItem.query.count() + 1
        item_code = data.get('item_code') or f"MAT-ITM-{str(count).zfill(2)}"

        exp_date = None
        if data.get('expiry_date'):
            exp_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()

        item = InventoryItem(
            item_code=item_code,
            name=data.get('name'),
            category=data.get('category', 'Dental Materials'),
            current_stock=int(data.get('current_stock', 0)),
            min_stock_level=int(data.get('min_stock_level', 10)),
            unit=data.get('unit', 'units'),
            unit_price=float(data.get('unit_price', 0.0)),
            supplier_name=data.get('supplier_name', 'DentSupply Prime India'),
            batch_number=data.get('batch_number', 'BATCH-2026-X'),
            expiry_date=exp_date,
            branch_id=1
        )
        db.session.add(item)
        db.session.commit()

        # Add initial log
        log = InventoryLog(
            item_id=item.id,
            change_type='Add',
            quantity=item.current_stock,
            reason='Initial Stock Entry',
            performed_by=current_user.name
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Inventory item added', 'item': item.to_dict()}), 201

    category = request.args.get('category')
    low_stock = request.args.get('low_stock')
    query = InventoryItem.query

    if category and category != 'All':
        query = query.filter_by(category=category)
    if low_stock == 'true':
        query = query.filter(InventoryItem.current_stock <= InventoryItem.min_stock_level)

    items = query.order_by(InventoryItem.name.asc()).all()
    return jsonify({
        'items': [i.to_dict() for i in items],
        'total_items': len(items),
        'low_stock_count': sum(1 for i in items if i.current_stock <= i.min_stock_level),
        'total_inventory_value': sum(i.current_stock * i.unit_price for i in items)
    })

@inventory_bp.route('/api/inventory/<int:item_id>/adjust', methods=['POST'])
@login_required
def adjust_stock(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    data = request.get_json()
    change_type = data.get('change_type', 'Add') # Add, Deduct
    qty = int(data.get('quantity', 1))
    reason = data.get('reason', 'Routine usage')

    if change_type == 'Add':
        item.current_stock += qty
        item.last_restocked = datetime.utcnow()
    elif change_type == 'Deduct':
        item.current_stock = max(0, item.current_stock - qty)

    # Add log
    inv_log = InventoryLog(
        item_id=item.id,
        change_type=change_type,
        quantity=qty,
        reason=reason,
        performed_by=current_user.name
    )
    db.session.add(inv_log)
    db.session.commit()

    # Log audit
    audit = AuditLog(
        user_name=current_user.name,
        user_role=current_user.role,
        action=f"Stock {change_type} ({qty} {item.unit}) for '{item.name}' — {reason}",
        module="Inventory",
        ip_address=request.remote_addr or '127.0.0.1'
    )
    db.session.add(audit)
    db.session.commit()

    return jsonify({'status': 'success', 'message': f'Stock updated for {item.name}', 'item': item.to_dict()})

@inventory_bp.route('/api/inventory/purchase-orders', methods=['GET', 'POST'])
@login_required
def purchase_orders():
    if request.method == 'POST':
        data = request.get_json()
        count = PurchaseOrder.query.count() + 34
        po_no = f"PO-2026-{str(count).zfill(3)}"

        po = PurchaseOrder(
            po_number=po_no,
            supplier_name=data.get('supplier_name'),
            total_amount=float(data.get('total_amount', 0.0)),
            status='Ordered',
            items_summary=data.get('items_summary', 'Stock Replenishment'),
            order_date=datetime.utcnow(),
            expected_delivery=date.today() + timedelta(days=3)
        )
        db.session.add(po)
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'Purchase order {po.po_number} created', 'po': po.to_dict()}), 201

    pos = PurchaseOrder.query.order_by(PurchaseOrder.id.desc()).all()
    return jsonify({'purchase_orders': [p.to_dict() for p in pos]})
