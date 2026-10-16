from datetime import datetime
from app.extensions import db

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    sku = db.Column(db.String(60), unique=True, nullable=False, index=True)
    brand = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    cost_price = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    minimum_stock = db.Column(db.Integer, nullable=False, default=10)
    maximum_stock = db.Column(db.Integer, nullable=False, default=1000)
    image_url = db.Column(db.String(255), default='/static/img/default-product.png')
    status = db.Column(db.Enum('active', 'inactive', name='product_status'), default='active', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    inventory_items = db.relationship('Inventory', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic')
    stock_movements = db.relationship('StockMovement', backref='product', lazy='dynamic')
    alerts = db.relationship('Alert', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    po_items = db.relationship('PurchaseOrderItem', backref='product', lazy='dynamic')

    @property
    def total_stock(self):
        """Aggregate current stock across all warehouses"""
        total = db.session.query(db.func.sum(Inventory.quantity)).filter(Inventory.product_id == self.id).scalar()
        return int(total) if total is not None else 0

    @property
    def stock_status(self):
        qty = self.total_stock
        if qty <= 0:
            return 'Out of Stock'
        elif qty <= self.minimum_stock:
            return 'Low Stock'
        return 'In Stock'

    def to_dict(self, include_inventory=False):
        qty = self.total_stock
        status_label = self.stock_status
        data = {
            'id': self.id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else '',
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier.name if self.supplier else '',
            'name': self.name,
            'sku': self.sku,
            'brand': self.brand or '',
            'description': self.description or '',
            'price': float(self.price or 0.0),
            'cost_price': float(self.cost_price or 0.0),
            'minimum_stock': self.minimum_stock or 0,
            'maximum_stock': self.maximum_stock or 1000,
            'image_url': self.image_url or '/static/img/default-product.png',
            'status': self.status or 'active',
            'total_stock': qty,
            'stock_status': status_label,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_inventory:
            data['inventory'] = [inv.to_dict() for inv in self.inventory_items]
        return data

    def __repr__(self):
        return f'<Product {self.sku} - {self.name}>'

# Avoid circular dependency in property
from app.models.inventory import Inventory

