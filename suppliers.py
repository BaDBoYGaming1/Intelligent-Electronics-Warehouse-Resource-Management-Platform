from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.utils.auth import role_required, get_current_user
from app.utils.validators import validate_email
from app.utils.logger import audit_log

suppliers_bp = Blueprint('suppliers_api', __name__, url_prefix='/api/suppliers')

@suppliers_bp.route('', methods=['GET'])
@role_required('admin')
def list_suppliers():
    suppliers = Supplier.query.order_by(Supplier.name.asc()).all()
    return jsonify({
        'success': True,
        'suppliers': [s.to_dict() for s in suppliers]
    }), 200

@suppliers_bp.route('/<int:supplier_id>', methods=['GET'])
@role_required('admin')
def get_supplier(supplier_id):
    supplier = db.session.get(Supplier, supplier_id)
    if not supplier:
        return jsonify({'success': False, 'message': 'Supplier not found.'}), 404
    
    data = supplier.to_dict()
    data['products'] = [p.to_dict() for p in supplier.products]
    data['purchase_orders'] = [po.to_dict(include_items=False) for po in supplier.purchase_orders]
    return jsonify({'success': True, 'supplier': data}), 200

@suppliers_bp.route('', methods=['POST'])
@role_required('admin')
def create_supplier():
    user = get_current_user()
    data = request.get_json() or {}

    name = data.get('name', '').strip()
    contact_person = data.get('contact_person', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()

    if not name or not email:
        return jsonify({'success': False, 'message': 'Supplier name and email are required.'}), 400

    if not validate_email(email):
        return jsonify({'success': False, 'message': 'Valid email is required.'}), 400

    if Supplier.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'A supplier with this email already exists.'}), 409

    supplier = Supplier(
        name=name,
        contact_person=contact_person,
        email=email,
        phone=phone,
        address=address,
        status='active'
    )
    db.session.add(supplier)
    db.session.commit()

    audit_log("SUPPLIER_CREATED", user_id=user.id, details={'supplier_id': supplier.id, 'name': name})
    return jsonify({'success': True, 'message': 'Supplier created successfully.', 'supplier': supplier.to_dict()}), 201

@suppliers_bp.route('/<int:supplier_id>', methods=['PUT'])
@role_required('admin')
def update_supplier(supplier_id):
    user = get_current_user()
    supplier = db.session.get(Supplier, supplier_id)
    if not supplier:
        return jsonify({'success': False, 'message': 'Supplier not found.'}), 404

    data = request.get_json() or {}
    if 'name' in data and data['name']:
        supplier.name = data['name'].strip()
    if 'contact_person' in data:
        supplier.contact_person = data['contact_person'].strip()
    if 'phone' in data:
        supplier.phone = data['phone'].strip()
    if 'address' in data:
        supplier.address = data['address'].strip()
    if 'status' in data and data['status'] in ['active', 'inactive']:
        supplier.status = data['status']

    db.session.commit()
    audit_log("SUPPLIER_UPDATED", user_id=user.id, details={'supplier_id': supplier.id})
    return jsonify({'success': True, 'message': 'Supplier updated successfully.', 'supplier': supplier.to_dict()}), 200

@suppliers_bp.route('/<int:supplier_id>', methods=['DELETE'])
@role_required('admin')
def deactivate_supplier(supplier_id):
    user = get_current_user()
    supplier = db.session.get(Supplier, supplier_id)
    if not supplier:
        return jsonify({'success': False, 'message': 'Supplier not found.'}), 404

    supplier.status = 'inactive'
    db.session.commit()
    audit_log("SUPPLIER_DEACTIVATED", user_id=user.id, details={'supplier_id': supplier.id})
    return jsonify({'success': True, 'message': f"Supplier '{supplier.name}' deactivated."}), 200

