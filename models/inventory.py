from datetime import datetime
from . import db

class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    rating = db.Column(db.Float, default=4.8)
    payment_terms = db.Column(db.String(50), default='Net 30 Days')

    items = db.relationship('InventoryItem', backref='supplier_rel', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'rating': self.rating,
            'payment_terms': self.payment_terms
        }

class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'

    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(30), unique=True, nullable=False) # e.g. "INV-MAT-01"
    name = db.Column(db.String(100), nullable=False) # e.g. "Composite Resin A2", "Latex Gloves"
    category = db.Column(db.String(50), nullable=False) # Dental Materials, Consumables, Lab Materials, Medicines, Equipment
    current_stock = db.Column(db.Integer, nullable=False, default=0)
    min_stock_level = db.Column(db.Integer, nullable=False, default=10)
    unit = db.Column(db.String(30), default='units') # units, boxes, packs, bottles, kits
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    supplier_name = db.Column(db.String(100), default='DentSupply India Ltd')
    batch_number = db.Column(db.String(50), default='BATCH-2026-X')
    expiry_date = db.Column(db.Date, nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    last_restocked = db.Column(db.DateTime, default=datetime.utcnow)

    logs = db.relationship('InventoryLog', backref='item', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        is_low_stock = self.current_stock <= self.min_stock_level
        status = 'Critical' if self.current_stock == 0 else ('Low Stock' if is_low_stock else 'Healthy')
        return {
            'id': self.id,
            'item_code': self.item_code,
            'name': self.name,
            'category': self.category,
            'current_stock': self.current_stock,
            'min_stock_level': self.min_stock_level,
            'unit': self.unit,
            'unit_price': self.unit_price,
            'total_value': self.current_stock * self.unit_price,
            'supplier_name': self.supplier_name,
            'batch_number': self.batch_number,
            'expiry_date': self.expiry_date.strftime('%d %b %Y') if self.expiry_date else 'N/A',
            'is_low_stock': is_low_stock,
            'status': status,
            'last_restocked': self.last_restocked.strftime('%d %b %Y') if self.last_restocked else ''
        }

class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'

    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(30), unique=True, nullable=False) # e.g. "PO-2026-033"
    supplier_name = db.Column(db.String(100), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Ordered') # Draft, Ordered, Received, Cancelled
    items_summary = db.Column(db.String(255), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    expected_delivery = db.Column(db.Date, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'po_number': self.po_number,
            'supplier_name': self.supplier_name,
            'total_amount': self.total_amount,
            'status': self.status,
            'items_summary': self.items_summary,
            'order_date': self.order_date.strftime('%d %b %Y'),
            'expected_delivery': self.expected_delivery.strftime('%d %b %Y') if self.expected_delivery else 'In 3 days'
        }

class InventoryLog(db.Model):
    __tablename__ = 'inventory_logs'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    change_type = db.Column(db.String(30), nullable=False) # 'Add', 'Deduct', 'Adjustment', 'Disposed'
    quantity = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=True) # e.g. "Restocked via PO", "Used in RCT procedure Chair 02"
    performed_by = db.Column(db.String(100), default='Dr. Sharma')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'item_name': self.item.name if self.item else '',
            'change_type': self.change_type,
            'quantity': self.quantity,
            'reason': self.reason,
            'performed_by': self.performed_by,
            'created_at': self.created_at.strftime('%d %b %Y, %I:%M %p')
        }
