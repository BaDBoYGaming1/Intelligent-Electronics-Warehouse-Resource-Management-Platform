from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.category import Category
from app.utils.auth import role_required, get_current_user

categories_bp = Blueprint('categories_api', __name__, url_prefix='/api/categories')

@categories_bp.route('', methods=['GET'])
def list_categories():
    categories = Category.query.order_by(Category.name.asc()).all()
    return jsonify({
        'success': True,
        'categories': [c.to_dict() for c in categories]
    }), 200

@categories_bp.route('', methods=['POST'])
@role_required('admin')
def create_category():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    icon = data.get('icon', 'bi-cpu').strip()

    if not name:
        return jsonify({'success': False, 'message': 'Category name is required.'}), 400

    if Category.query.filter_by(name=name).first():
        return jsonify({'success': False, 'message': f"Category '{name}' already exists."}), 409

    cat = Category(name=name, description=description, icon=icon)
    db.session.add(cat)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Category created successfully.',
        'category': cat.to_dict()
    }), 201

