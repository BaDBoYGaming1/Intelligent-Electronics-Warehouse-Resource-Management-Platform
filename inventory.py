from flask import Blueprint, request, jsonify
from sqlalchemy import or_, desc
from app.extensions import db
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.stock_movement import StockMovement
from app.services.inventory_service import adjust_stock
from app.utils.auth import role_required, get_current_user

inventory_bp = Blueprint('inventory_api', __name__, url_prefix='/api/inventory')

@inventory_bp.route('', methods=['GET'])
@role_required('admin', 'employee')
def list_inventory():
    """
    Warehouse inventory tracking list.
    Supports filtering by search query, warehouse_id, and stock status ('low', 'out', 'in').
    """
    page = request.args.get('page', 1, type=int)
    limit = min(request.args.get('limit', 20, type=int), 100)
    search = request.args.get('q', '').strip()
    warehouse_id = request.args.get('warehouse_id', type=int)
    status_filter = request.args.get('status', '').strip().lower()

    query = Inventory.query.join(Product)

    if warehouse_id:
        query = query.filter(Inventory.warehouse_id == warehouse_id)

    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%"),
                Product.brand.ilike(f"%{search}%")
            )
        )

    if status_filter == 'out':
        query = query.filter(Inventory.quantity == 0)
    elif status_filter == 'low':
        query = query.filter(Inventory.quantity > 0, Inventory.quantity <= Product.minimum_stock)
    elif status_filter == 'in':
        query = query.filter(Inventory.quantity > Product.minimum_stock)

    pagination = query.order_by(Product.name.asc()).paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        'success': True,
        'inventory': [item.to_dict() for item in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages
    }), 200


@inventory_bp.route('/adjust', methods=['POST'])
@role_required('admin', 'employee')
def record_stock_adjustment():
    """
    Manual stock adjustments (Received, Damaged, Returned, Adjusted, Transfer).
    Executes within an atomic transaction with row-level locking.
    """
    user = get_current_user()
    data = request.get_json() or {}

    product_id = data.get('product_id')
    warehouse_id = data.get('warehouse_id')
    quantity_change = data.get('quantity_change')
    movement_type = data.get('movement_type', 'ADJUSTMENT').upper()
    notes = data.get('notes', '')

    if not product_id or not warehouse_id or quantity_change is None:
        return jsonify({'success': False, 'message': 'Product, Warehouse, and Quantity Change are required.'}), 400

    try:
        quantity_change = int(quantity_change)
        if quantity_change == 0:
            return jsonify({'success': False, 'message': 'Quantity change cannot be 0.'}), 400

        # Enforce positive delta for Received/Return and negative for Damaged
        if movement_type in ['PURCHASE', 'RETURN'] and quantity_change < 0:
            quantity_change = abs(quantity_change)
        elif movement_type == 'DAMAGE' and quantity_change > 0:
            quantity_change = -abs(quantity_change)

        movement, new_stock = adjust_stock(
            product_id=int(product_id),
            warehouse_id=int(warehouse_id),
            quantity_change=quantity_change,
            movement_type=movement_type,
            user_id=user.id,
            reference_type='MANUAL_ADJUSTMENT',
            reference_id=None,
            notes=notes
        )
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f"Stock adjusted successfully. New stock: {new_stock} units.",
            'movement': movement.to_dict(),
            'new_stock': new_stock
        }), 200

    except ValueError as ve:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(ve)}), 400
    except Exception as ex:
        db.session.rollback()
        return jsonify({'success': False, 'message': f"Adjustment failed: {str(ex)}"}), 500


@inventory_bp.route('/movements', methods=['GET'])
@role_required('admin', 'employee')
def list_stock_movements():
    """
    Audit trail listing of all stock movements.
    """
    page = request.args.get('page', 1, type=int)
    limit = min(request.args.get('limit', 20, type=int), 100)
    movement_type = request.args.get('type', '').strip().upper()
    product_id = request.args.get('product_id', type=int)

    query = StockMovement.query
    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type)
    if product_id:
        query = query.filter(StockMovement.product_id == product_id)

    pagination = query.order_by(desc(StockMovement.created_at)).paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        'success': True,
        'movements': [m.to_dict() for m in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages
    }), 200


@inventory_bp.route('/warehouses', methods=['GET'])
@role_required('admin', 'employee')
def list_warehouses():
    warehouses = Warehouse.query.all()
    return jsonify({
        'success': True,
        'warehouses': [w.to_dict() for w in warehouses]
    }), 200

