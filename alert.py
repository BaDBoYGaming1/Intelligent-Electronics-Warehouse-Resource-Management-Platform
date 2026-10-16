from datetime import datetime
from app.extensions import db

class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    alert_type = db.Column(db.Enum('LOW_STOCK', 'OUT_OF_STOCK', name='alert_types'), nullable=False, default='LOW_STOCK')
    current_stock = db.Column(db.Integer, nullable=False)
    threshold = db.Column(db.Integer, nullable=False)
    recommended_order = db.Column(db.Integer, nullable=False, default=20)
    status = db.Column(db.Enum('ACTIVE', 'RESOLVED', name='alert_statuses'), nullable=False, default='ACTIVE', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else '',
            'sku': self.product.sku if self.product else '',
            'category_name': self.product.category.name if self.product and self.product.category else '',
            'supplier_id': self.product.supplier_id if self.product else None,
            'supplier_name': self.product.supplier.name if self.product and self.product.supplier else '',
            'warehouse_id': self.warehouse_id,
            'warehouse_name': self.warehouse.name if self.warehouse else '',
            'alert_type': self.alert_type,
            'current_stock': self.current_stock,
            'threshold': self.threshold,
            'recommended_order': self.recommended_order,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }

    def __repr__(self):
        return f'<Alert {self.alert_type} Prod:{self.product_id} Status:{self.status}>'

