from datetime import datetime
from app.extensions import db

class Inventory(db.Model):
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('product_id', 'warehouse_id', name='uq_product_warehouse'),
        db.CheckConstraint('quantity >= 0', name='chk_inventory_qty')
    )

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else '',
            'sku': self.product.sku if self.product else '',
            'warehouse_id': self.warehouse_id,
            'warehouse_name': self.warehouse.name if self.warehouse else '',
            'warehouse_code': self.warehouse.code if self.warehouse else '',
            'quantity': self.quantity,
            'minimum_stock': self.product.minimum_stock if self.product else 10,
            'maximum_stock': self.product.maximum_stock if self.product else 1000,
            'stock_status': (
                'Out of Stock' if self.quantity == 0 
                else ('Low Stock' if self.quantity <= (self.product.minimum_stock if self.product else 10) 
                else 'In Stock')
            ),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Inventory Prod:{self.product_id} Whse:{self.warehouse_id} Qty:{self.quantity}>'

