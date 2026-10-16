from datetime import datetime
from app.extensions import db

class Warehouse(db.Model):
    __tablename__ = 'warehouses'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    location = db.Column(db.String(200), nullable=False)
    capacity = db.Column(db.Integer, default=50000)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    inventory_items = db.relationship('Inventory', backref='warehouse', lazy='dynamic')
    stock_movements = db.relationship('StockMovement', backref='warehouse', lazy='dynamic')
    alerts = db.relationship('Alert', backref='warehouse', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'location': self.location,
            'capacity': self.capacity,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Warehouse {self.code} - {self.name}>'

