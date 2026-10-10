from flask import Blueprint, request, jsonify
from sqlalchemy import or_, desc
from app.extensions import db
from app.models.order import Order
from app.utils.auth import token_or_session_required, role_required, get_current_user
from app.services.order_service import create_order_transaction, update_order_status
from app.utils.logger import audit_log

orders_bp = Blueprint('orders_api', __name__, url_prefix='/api/orders')

@orders_bp.route('', methods=['POST'])
@role_required('customer')
def checkout():
    """
    Transactional Checkout Endpoint:
    Accepts cart items, customer shipping address, and simulated payment method.
    Atomic transaction guarantees no negative stock, no partial orders, and complete audit trail.
    Strictly restricted to authenticated customer accounts.
    """
    user = get_current_user()
    data = request.get_json() or {}

    items = data.get('items', [])
    shipping_address = data.get('shipping_address') or user.address
    payment_method = data.get('payment_method', 'card')
    notes = data.get('notes', '')

    if not isinstance(items, list) or len(items) == 0:
        return jsonify({'success': False, 'message': 'Cart cannot be empty.'}), 400

    # Server-side validation of item payloads
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            return jsonify({'success': False, 'message': f'Invalid item format at position {idx}.'}), 400
        prod_id = item.get('product_id')
        qty = item.get('quantity')
        if prod_id is None or not (isinstance(prod_id, int) or (isinstance(prod_id, str) and str(prod_id).isdigit())) or int(prod_id) <= 0:
            return jsonify({'success': False, 'message': f'Invalid product ID at item position {idx}.'}), 400
        if qty is None or not isinstance(qty, int) or qty <= 0:
            return jsonify({'success': False, 'message': f'Quantity for each product must be a positive integer greater than zero.'}), 400

    if not shipping_address or not str(shipping_address).strip():
        return jsonify({'success': False, 'message': 'Shipping address is required.'}), 400

    try:
        order = create_order_transaction(
            customer_id=user.id,
            items_data=items,
            shipping_address=shipping_address,
            payment_method=payment_method,
            notes=notes
        )

        return jsonify({
            'success': True,
            'message': f"Order #{order.order_number} placed successfully!",
            'order': order.to_dict(include_items=True)
        }), 201

    except ValueError as ve:
        return jsonify({'success': False, 'message': str(ve)}), 400
    except Exception as ex:
        return jsonify({
            'success': False,
            'message': f"Transaction failed and was safely rolled back: {str(ex)}"
        }), 500


@orders_bp.route('', methods=['GET'])
@token_or_session_required
def list_orders():
    """
    Lists orders. Customers see only their own orders.
    Employees and Admins can view all orders, filter by status, search, and paginate.
    """
    user = get_current_user()
    page = request.args.get('page', 1, type=int)
    limit = min(request.args.get('limit', 15, type=int), 100)
    status = request.args.get('status', '').strip()
    search = request.args.get('q', '').strip()

    query = Order.query

    # Role constraint
    if user.role == 'customer':
        query = query.filter_by(customer_id=user.id)

    if status:
        query = query.filter(Order.status == status)

    if search:
        query = query.filter(
            or_(
                Order.order_number.ilike(f"%{search}%"),
                Order.shipping_address.ilike(f"%{search}%")
            )
        )

    pagination = query.order_by(desc(Order.created_at)).paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        'success': True,
        'orders': [o.to_dict(include_items=True) for o in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages
    }), 200


@orders_bp.route('/<int:order_id>', methods=['GET'])
@token_or_session_required
def get_order_detail(order_id):
    user = get_current_user()
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found.'}), 404

    # Authorization: Customers can only view their own order
    if user.role == 'customer' and order.customer_id != user.id:
        return jsonify({'success': False, 'message': 'Unauthorized to view this order.'}), 403

    return jsonify({
        'success': True,
        'order': order.to_dict(include_items=True)
    }), 200


@orders_bp.route('/<int:order_id>/status', methods=['PATCH'])
@role_required('admin', 'employee')
def change_order_status(order_id):
    """
    Warehouse staff / Admin updates order fulfillment status.
    If status is changed to Cancelled, stock is automatically returned inside a transaction.
    """
    user = get_current_user()
    data = request.get_json() or {}
    new_status = data.get('status')

    if not new_status:
        return jsonify({'success': False, 'message': 'New status is required.'}), 400

    try:
        updated_order = update_order_status(
            order_id=order_id,
            new_status=new_status,
            employee_user_id=user.id
        )
        return jsonify({
            'success': True,
            'message': f"Order #{updated_order.order_number} status updated to {new_status}.",
            'order': updated_order.to_dict(include_items=True)
        }), 200
    except ValueError as ve:
        return jsonify({'success': False, 'message': str(ve)}), 400
    except Exception as ex:
        return jsonify({'success': False, 'message': str(ex)}), 500

