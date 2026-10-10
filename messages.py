from flask import Blueprint, request, jsonify
from sqlalchemy import or_, desc
from app.extensions import db
from app.models.message import Message
from app.models.user import User
from app.models.product import Product
from app.utils.auth import token_or_session_required, role_required, get_current_user
from app.utils.logger import audit_log

messages_bp = Blueprint('messages_api', __name__, url_prefix='/api/messages')

@messages_bp.route('', methods=['GET'])
@role_required('admin', 'employee')
def list_messages():
    """
    Returns messages relevant to the logged-in user:
    - Admin sees incoming employee alerts and direct queries.
    - Employee sees threads they participated in.
    """
    user = get_current_user()

    # Get parent threads
    if user.role == 'admin':
        # Admin sees all parent messages
        query = Message.query.filter(Message.parent_id.is_(None))
    else:
        # Employee sees messages they sent or were addressed to them
        query = Message.query.filter(
            Message.parent_id.is_(None),
            or_(Message.sender_id == user.id, Message.recipient_id == user.id)
        )

    threads = query.order_by(desc(Message.created_at)).all()

    return jsonify({
        'success': True,
        'messages': [m.to_dict(include_replies=True) for m in threads],
        'unread_count': Message.query.filter_by(recipient_id=user.id, is_read=False).count()
    }), 200


@messages_bp.route('/unread-count', methods=['GET'])
@role_required('admin', 'employee')
def unread_count():
    user = get_current_user()
    count = Message.query.filter_by(recipient_id=user.id, is_read=False).count()
    return jsonify({'success': True, 'unread_count': count}), 200


@messages_bp.route('', methods=['POST'])
@role_required('admin', 'employee')
def send_message():
    user = get_current_user()
    data = request.get_json() or {}

    subject = data.get('subject', '').strip()
    content = data.get('message', '').strip()
    product_id = data.get('product_id')
    recipient_id = data.get('recipient_id')
    parent_id = data.get('parent_id')

    if not subject or not content:
        return jsonify({'success': False, 'message': 'Subject and message body are required.'}), 400

    # If recipient not explicitly set:
    # If employee sending: route to primary admin
    if not recipient_id:
        if user.role == 'employee':
            admin_user = User.query.filter_by(role='admin').first()
            if not admin_user:
                return jsonify({'success': False, 'message': 'No administrator account configured.'}), 500
            recipient_id = admin_user.id
        else:
            # If admin replying to a parent thread
            if parent_id:
                parent_msg = db.session.get(Message, parent_id)
                if parent_msg:
                    recipient_id = parent_msg.sender_id
            if not recipient_id:
                return jsonify({'success': False, 'message': 'Recipient is required.'}), 400

    new_msg = Message(
        sender_id=user.id,
        recipient_id=recipient_id,
        product_id=int(product_id) if product_id else None,
        subject=subject,
        message=content,
        parent_id=int(parent_id) if parent_id else None,
        is_read=False
    )
    db.session.add(new_msg)
    db.session.commit()

    audit_log("MESSAGE_SENT", user_id=user.id, details={'recipient_id': recipient_id, 'subject': subject})

    return jsonify({
        'success': True,
        'message': 'Message dispatched successfully.',
        'msg': new_msg.to_dict()
    }), 201


@messages_bp.route('/<int:message_id>/read', methods=['PATCH'])
@role_required('admin', 'employee')
def mark_read(message_id):
    user = get_current_user()
    msg = db.session.get(Message, message_id)
    if not msg:
        return jsonify({'success': False, 'message': 'Message not found.'}), 404

    # Recipient can mark message as read
    if msg.recipient_id == user.id or user.role == 'admin':
        msg.is_read = True
        db.session.commit()

    return jsonify({'success': True, 'message': 'Marked as read.'}), 200

