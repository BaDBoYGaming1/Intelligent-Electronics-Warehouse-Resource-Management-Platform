import os
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import or_, desc, asc
from app.extensions import db
from app.models.product import Product
from app.models.category import Category
from app.models.inventory import Inventory
from app.models.warehouse import Warehouse
from app.models.order import OrderItem
from app.utils.auth import role_required, get_current_user
from app.utils.validators import save_secure_file
from app.utils.logger import audit_log

products_bp = Blueprint('products_api', __name__, url_prefix='/api/products')

@products_bp.route('', methods=['GET'])
def list_products():
    """
    Public product catalog endpoint.
    Supports search (name, brand, sku), category filter, price range, sorting, and pagination.
    """
    page = request.args.get('page', 1, type=int)
    limit = min(request.args.get('limit', 12, type=int), 100)
    search_query = request.args.get('q', '').strip()
    category_id = request.args.get('category', type=int)
    brand = request.args.get('brand', '').strip()
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort', 'newest')
    status_filter = request.args.get('status', 'active')

    # Allow admins to see inactive products
    current_user = get_current_user()
    if not (current_user and current_user.role in ['admin', 'employee']):
        status_filter = 'active'

    query = Product.query
    if status_filter != 'all':
        query = query.filter(Product.status == status_filter)

    # Full-text / LIKE search across name, SKU, brand, and description
    if search_query:
        term = f"%{search_query}%"
        query = query.filter(
            or_(
                Product.name.ilike(term),
                Product.sku.ilike(term),
                Product.brand.ilike(term),
                Product.description.ilike(term)
            )
        )

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # Sorting
    if sort_by == 'price_asc':
        query = query.order_by(asc(Product.price))
    elif sort_by == 'price_desc':
        query = query.order_by(desc(Product.price))
    elif sort_by == 'popularity':
        # Sort by total units ordered
        query = query.outerjoin(OrderItem).group_by(Product.id).order_by(desc(db.func.sum(OrderItem.quantity)))
    else:
        query = query.order_by(desc(Product.created_at))

    pagination = query.paginate(page=page, per_page=limit, error_out=False)
    products = [p.to_dict() for p in pagination.items]

    return jsonify({
        'success': True,
        'products': products,
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'limit': limit
    }), 200


@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found.'}), 404

    current_user = get_current_user()
    include_inv = bool(current_user and current_user.role in ['admin', 'employee'])
    return jsonify({
        'success': True,
        'product': product.to_dict(include_inventory=include_inv)
    }), 200


@products_bp.route('', methods=['POST'])
@role_required('admin')
def create_product():
    """
    Admin product creation with optional product image file upload.
    OS File Management validation applied to uploaded images.
    """
    user = get_current_user()
    
    # Check if form data or JSON
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form
        image_file = request.files.get('image')
    else:
        data = request.get_json() or {}
        image_file = None

    name = data.get('name', '').strip()
    sku = data.get('sku', '').strip().upper()
    brand = data.get('brand', '').strip()
    category_id = data.get('category_id')
    price = data.get('price')
    cost_price = data.get('cost_price', 0.0)
    minimum_stock = int(data.get('minimum_stock', 10))
    maximum_stock = int(data.get('maximum_stock', 1000))
    initial_stock = int(data.get('initial_stock', 0))
    supplier_id = data.get('supplier_id')
    description = data.get('description', '').strip()

    if not name or not sku or not category_id or price is None:
        return jsonify({'success': False, 'message': 'Name, SKU, Category, and Price are required.'}), 400

    # SKU Uniqueness Check
    if Product.query.filter_by(sku=sku).first():
        return jsonify({'success': False, 'message': f"A product with SKU '{sku}' already exists."}), 409

    image_url = '/static/img/default-product.png'
    if image_file:
        success, err, uploaded_url = save_secure_file(
            image_file,
            current_app.config['UPLOAD_FOLDER'],
            current_app.config['ALLOWED_EXTENSIONS'],
            current_app.config['MAX_CONTENT_LENGTH']
        )
        if not success:
            return jsonify({'success': False, 'message': err}), 400
        image_url = uploaded_url
    elif data.get('image_url'):
        image_url = data.get('image_url')

    new_product = Product(
        name=name,
        sku=sku,
        brand=brand or 'General',
        category_id=int(category_id),
        supplier_id=int(supplier_id) if supplier_id else None,
        price=float(price),
        cost_price=float(cost_price),
        minimum_stock=minimum_stock,
        maximum_stock=maximum_stock,
        description=description,
        image_url=image_url,
        status='active'
    )
    db.session.add(new_product)
    db.session.flush()

    # Create initial inventory record in default warehouse
    primary_warehouse = Warehouse.query.first()
    if primary_warehouse:
        inv = Inventory(
            product_id=new_product.id,
            warehouse_id=primary_warehouse.id,
            quantity=initial_stock
        )
        db.session.add(inv)

    db.session.commit()
    audit_log("PRODUCT_CREATED", user_id=user.id, details={'product_id': new_product.id, 'sku': sku})

    return jsonify({
        'success': True,
        'message': 'Product created successfully.',
        'product': new_product.to_dict()
    }), 201


@products_bp.route('/<int:product_id>', methods=['PUT'])
@role_required('admin')
def update_product(product_id):
    user = get_current_user()
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found.'}), 404

    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form
        image_file = request.files.get('image')
    else:
        data = request.get_json() or {}
        image_file = None

    if 'name' in data and data['name']:
        product.name = data['name'].strip()
    if 'brand' in data:
        product.brand = data['brand'].strip()
    if 'category_id' in data and data['category_id']:
        product.category_id = int(data['category_id'])
    if 'supplier_id' in data:
        product.supplier_id = int(data['supplier_id']) if data['supplier_id'] else None
    if 'price' in data and data['price'] is not None:
        product.price = float(data['price'])
    if 'cost_price' in data and data['cost_price'] is not None:
        product.cost_price = float(data['cost_price'])
    if 'minimum_stock' in data and data['minimum_stock'] is not None:
        product.minimum_stock = int(data['minimum_stock'])
    if 'maximum_stock' in data and data['maximum_stock'] is not None:
        product.maximum_stock = int(data['maximum_stock'])
    if 'description' in data:
        product.description = data['description'].strip()
    if 'status' in data and data['status'] in ['active', 'inactive']:
        product.status = data['status']

    if image_file:
        success, err, uploaded_url = save_secure_file(
            image_file,
            current_app.config['UPLOAD_FOLDER'],
            current_app.config['ALLOWED_EXTENSIONS'],
            current_app.config['MAX_CONTENT_LENGTH']
        )
        if not success:
            return jsonify({'success': False, 'message': err}), 400
        product.image_url = uploaded_url
    elif data.get('image_url'):
        product.image_url = data.get('image_url')

    db.session.commit()
    audit_log("PRODUCT_UPDATED", user_id=user.id, details={'product_id': product.id, 'sku': product.sku})

    return jsonify({
        'success': True,
        'message': 'Product updated successfully.',
        'product': product.to_dict()
    }), 200


@products_bp.route('/<int:product_id>', methods=['DELETE'])
@role_required('admin')
def delete_product(product_id):
    """
    Safe deletion: If historical order items reference this product, soft-deactivate instead of deleting.
    Preserves relational integrity in accordance with DBMS foreign key constraints.
    """
    user = get_current_user()
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found.'}), 404

    order_items_count = OrderItem.query.filter_by(product_id=product_id).count()
    if order_items_count > 0:
        product.status = 'inactive'
        db.session.commit()
        audit_log("PRODUCT_DEACTIVATED", user_id=user.id, details={'product_id': product.id, 'sku': product.sku})
        return jsonify({
            'success': True,
            'message': f"Product '{product.name}' has historical sales orders and was safely deactivated instead of deleted."
        }), 200

    db.session.delete(product)
    db.session.commit()
    audit_log("PRODUCT_DELETED", user_id=user.id, details={'product_id': product_id})

    return jsonify({'success': True, 'message': 'Product deleted successfully.'}), 200

