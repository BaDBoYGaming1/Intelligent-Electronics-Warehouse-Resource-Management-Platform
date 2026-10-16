from datetime import datetime
from app.extensions import db

class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    po_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False, index=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    status = db.Column(
        db.Enum('Draft', 'Ordered', 'Received', 'Cancelled', name='po_statuses'),
        nullable=False,
        default='Draft',
        index=True
    )
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    expected_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('PurchaseOrderItem', backref='purchase_order', lazy='joined', cascade='all, delete-orphan')

    def to_dict(self, include_items=True):
        data = {
            'id': self.id,
            'po_number': self.po_number,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier.name if self.supplier else '',
            'supplier_email': self.supplier.email if self.supplier else '',
            'total_amount': float(self.total_amount),
            'status': self.status,
            'notes': self.notes or '',
            'created_by': self.created_by,
            'creator_name': self.creator.full_name if self.creator else '',
            'expected_date': self.expected_date.isoformat() if self.expected_date else None,
            'item_count': len(self.items) if self.items else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_items:
            data['items'] = [item.to_dict() for item in self.items]
        return data

    def __repr__(self):
        return f'<PurchaseOrder {self.po_number} ({self.status})>'


class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchase_order_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_cost = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    __table_args__ = (
        db.CheckConstraint('quantity > 0', name='chk_poi_qty'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'po_id': self.po_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else '',
            'sku': self.product.sku if self.product else '',
            'quantity': self.quantity,
            'unit_cost': float(self.unit_cost),
            'subtotal': float(self.subtotal)
        }

    def __repr__(self):
        return f'<PurchaseOrderItem PO:{self.po_id} Prod:{self.product_id} Qty:{self.quantity}>'

