from datetime import datetime
from app.extensions import db

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('messages.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    replies = db.relationship('Message', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    product = db.relationship('Product', backref='messages')

    def to_dict(self, include_replies=False):
        data = {
            'id': self.id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.full_name if self.sender else 'Unknown',
            'sender_role': self.sender.role if self.sender else '',
            'recipient_id': self.recipient_id,
            'recipient_name': self.recipient.full_name if self.recipient else 'Unknown',
            'recipient_role': self.recipient.role if self.recipient else '',
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else '',
            'product_sku': self.product.sku if self.product else '',
            'subject': self.subject,
            'message': self.message,
            'is_read': self.is_read,
            'parent_id': self.parent_id,
            'reply_count': self.replies.count() if hasattr(self, 'replies') else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_replies:
            data['replies'] = [r.to_dict(include_replies=False) for r in self.replies.order_by(Message.created_at.asc())]
        return data

    def __repr__(self):
        return f'<Message {self.id} from {self.sender_id} to {self.recipient_id}: {self.subject}>'

