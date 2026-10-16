from datetime import datetime
from app.extensions import db

class StockMovement(db.Model):
    __tablename__ = 'stock_movements'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False, index=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    movement_type = db.Column(
        db.Enum('PURCHASE', 'SALE', 'RETURN', 'DAMAGE', 'ADJUSTMENT', 'TRANSFER', name='movement_types'),
        nullable=False,
        index=True
    )
    quantity = db.Column(db.Integer, nullable=False)
    previous_stock = db.Column(db.Integer, nullable=False)
    new_stock = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    reference_type = db.Column(db.String(50), nullable=True)  # e.g., 'ORDER', 'PO', 'MANUAL'
    reference_id = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = db.relationship('User', backref='stock_movements')

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else '',
            'sku': self.product.sku if self.product else '',
            'warehouse_id': self.warehouse_id,
            'warehouse_name': self.warehouse.name if self.warehouse else '',
            'movement_type': self.movement_type,
            'quantity': self.quantity,
            'previous_stock': self.previous_stock,
            'new_stock': self.new_stock,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else 'System',
            'reference_type': self.reference_type or '',
            'reference_id': self.reference_id,
            'notes': self.notes or '',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<StockMovement {self.movement_type} Prod:{self.product_id} Qty:{self.quantity}>'

