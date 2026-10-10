import uuid
from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.services.inventory_service import adjust_stock
from app.services.alert_service import check_product_stock_alert
from app.utils.auth import role_required, get_current_user
from app.utils.logger import audit_log

purchase_orders_bp = Blueprint('purchase_orders_api', __name__, url_prefix='/api/purchase-orders')

def generate_po_number():
    timestamp = datetime.utcnow().strftime('%Y%m%d')
    unique_suffix = uuid.uuid4().hex[:5].upper()
    return f"PO-{timestamp}-{unique_suffix}"

@purchase_orders_bp.route('', methods=['GET'])
@role_required('admin')
def list_purchase_orders():
    pos = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).all()
    return jsonify({
        'success': True,
        'purchase_orders': [po.to_dict(include_items=True) for po in pos]
    }), 200

@purchase_orders_bp.route('/<int:po_id>', methods=['GET'])
@role_required('admin')
def get_purchase_order(po_id):
    po = db.session.get(PurchaseOrder, po_id)
    if not po:
        return jsonify({'success': False, 'message': 'Purchase order not found.'}), 404
    return jsonify({'success': True, 'purchase_order': po.to_dict(include_items=True)}), 200

@purchase_orders_bp.route('', methods=['POST'])
@role_required('admin')
def create_purchase_order():
    user = get_current_user()
    data = request.get_json() or {}

    supplier_id = data.get('supplier_id')
    items = data.get('items', [])
    notes = data.get('notes', '')
    expected_date_str = data.get('expected_date')

    if not supplier_id or not items:
        return jsonify({'success': False, 'message': 'Supplier and at least one item are required.'}), 400

    supplier = db.session.get(Supplier, supplier_id)
    if not supplier:
        return jsonify({'success': False, 'message': 'Supplier not found.'}), 404

    expected_date = None
    if expected_date_str:
        try:
            expected_date = datetime.strptime(expected_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    total_amount = Decimal('0.00')
    po_items = []

    for item in items:
        product_id = int(item['product_id'])
        quantity = int(item.get('quantity', 1))
        unit_cost = Decimal(str(item.get('unit_cost', 0.0)))
        
        if quantity <= 0:
            return jsonify({'success': False, 'message': 'Item quantity must be greater than zero.'}), 400

        subtotal = unit_cost * quantity
        total_amount += subtotal
        po_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_cost': unit_cost,
            'subtotal': subtotal
        })

    po_number = generate_po_number()
    po = PurchaseOrder(
        po_number=po_number,
        supplier_id=supplier_id,
        total_amount=total_amount,
        status='Draft',
        notes=notes,
        created_by=user.id,
        expected_date=expected_date,
        created_at=datetime.utcnow()
    )
    db.session.add(po)
    db.session.flush()

    for item in po_items:
        poi = PurchaseOrderItem(
            po_id=po.id,
            product_id=item['product_id'],
            quantity=item['quantity'],
            unit_cost=item['unit_cost'],
            subtotal=item['subtotal']
        )
        db.session.add(poi)

    db.session.commit()
    audit_log("PO_CREATED", user_id=user.id, details={'po_number': po_number, 'supplier_id': supplier_id})

    return jsonify({
        'success': True,
        'message': f"Purchase Order #{po_number} created successfully.",
        'purchase_order': po.to_dict(include_items=True)
    }), 201


@purchase_orders_bp.route('/<int:po_id>/status', methods=['PATCH'])
@role_required('admin')
def update_po_status(po_id):
    """
    Handles PO status changes:
    - If status changes to 'Received':
      Executes atomic database transaction with row locking:
      1. Increases warehouse inventory for each product
      2. Creates StockMovement records (type: 'PURCHASE')
      3. Resolves low-stock alerts
      4. Marks PO as 'Received'
    Guards against concurrent duplicate receiving and terminal state transitions.
    """
    user = get_current_user()
    data = request.get_json() or {}
    new_status = data.get('status')
    if new_status not in ['Draft', 'Ordered', 'Received', 'Cancelled']:
        return jsonify({'success': False, 'message': 'Invalid PO status. Allowed: Draft, Ordered, Received, Cancelled'}), 400

    from app.services.order_service import _sqlite_lock
    is_sqlite = db.engine.dialect.name == 'sqlite'
    if is_sqlite:
        _sqlite_lock.acquire()

    try:
        # Pessimistic row locking on Purchase Order
        po = db.session.query(PurchaseOrder).filter_by(id=po_id).with_for_update().first()
        if not po:
            return jsonify({'success': False, 'message': 'Purchase order not found.'}), 404

        if po.status == 'Received':
            return jsonify({'success': False, 'message': 'Purchase order is already received and inventory was already added.'}), 400

        if po.status == 'Cancelled':
            return jsonify({'success': False, 'message': 'Cannot modify status of a Cancelled purchase order.'}), 400

        if po.status == new_status:
            return jsonify({'success': True, 'purchase_order': po.to_dict(include_items=True)}), 200

        primary_warehouse = Warehouse.query.first()
        warehouse_id = primary_warehouse.id if primary_warehouse else 1

        if new_status == 'Received':
            # Deadlock prevention: sort items by product_id
            sorted_items = sorted(po.items, key=lambda x: x.product_id)
            for item in sorted_items:
                adjust_stock(
                    product_id=item.product_id,
                    warehouse_id=warehouse_id,
                    quantity_change=item.quantity,
                    movement_type='PURCHASE',
                    user_id=user.id,
                    reference_type='PURCHASE_ORDER',
                    reference_id=po.id,
                    notes=f"Restock from PO #{po.po_number}"
                )

            po.status = 'Received'
            po.updated_at = datetime.utcnow()
            db.session.commit()

            audit_log("PO_RECEIVED", user_id=user.id, details={'po_number': po.po_number, 'items_count': len(po.items)})
            return jsonify({
                'success': True,
                'message': f"Purchase Order #{po.po_number} marked as Received. Inventory updated and low-stock alerts resolved!",
                'purchase_order': po.to_dict(include_items=True)
            }), 200

        else:
            po.status = new_status
            po.updated_at = datetime.utcnow()
            db.session.commit()
            audit_log("PO_STATUS_CHANGED", user_id=user.id, details={'po_number': po.po_number, 'to_status': new_status})
            return jsonify({
                'success': True,
                'message': f"Purchase Order #{po.po_number} status changed to {new_status}.",
                'purchase_order': po.to_dict(include_items=True)
            }), 200

    except Exception as ex:
        db.session.rollback()
        return jsonify({'success': False, 'message': f"Failed to update PO: {str(ex)}"}), 500
    finally:
        if is_sqlite:
            _sqlite_lock.release()

