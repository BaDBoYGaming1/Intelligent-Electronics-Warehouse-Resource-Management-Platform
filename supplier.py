from datetime import datetime
from app.extensions import db

class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    contact_person = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=True)
    address = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum('active', 'inactive', name='supplier_status'), default='active', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    products = db.relationship('Product', backref='supplier', lazy='dynamic')
    purchase_orders = db.relationship('PurchaseOrder', backref='supplier', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact_person': self.contact_person or '',
            'email': self.email,
            'phone': self.phone or '',
            'address': self.address or '',
            'status': self.status,
            'products_supplied_count': self.products.count() if hasattr(self, 'products') else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Supplier {self.name}>'

