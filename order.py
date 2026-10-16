from datetime import datetime
from app.extensions import db

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False, index=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    shipping_address = db.Column(db.Text, nullable=False)
    payment_method = db.Column(db.Enum('cod', 'card', 'upi', name='payment_methods'), nullable=False, default='card')
    payment_status = db.Column(db.Enum('paid', 'pending', 'failed', name='payment_statuses'), nullable=False, default='paid')
    status = db.Column(
        db.Enum('Pending', 'Confirmed', 'Processing', 'Shipped', 'Delivered', 'Cancelled', name='order_statuses'),
        nullable=False,
        default='Pending',
        index=True
    )
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='joined', cascade='all, delete-orphan')

    def to_dict(self, include_items=True):
        data = {
            'id': self.id,
            'order_number': self.order_number,
            'customer_id': self.customer_id,
            'customer_name': self.customer.full_name if self.customer else '',
            'customer_email': self.customer.email if self.customer else '',
            'total_amount': float(self.total_amount),
            'shipping_address': self.shipping_address,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'status': self.status,
            'notes': self.notes or '',
            'item_count': len(self.items) if self.items else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_items:
            data['items'] = [item.to_dict() for item in self.items]
        return data

    def __repr__(self):
        return f'<Order {self.order_number} ({self.status})>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    __table_args__ = (
        db.CheckConstraint('quantity > 0', name='chk_order_qty'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else '',
            'product_sku': self.product.sku if self.product else '',
            'product_image': self.product.image_url if self.product else '',
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'subtotal': float(self.subtotal)
        }

    def __repr__(self):
        return f'<OrderItem Order:{self.order_id} Prod:{self.product_id} Qty:{self.quantity}>'

