from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import create_access_token
from app.extensions import db
from app.models.user import User
from app.utils.auth import get_current_user, token_or_session_required
from app.utils.validators import validate_email, validate_password
from app.utils.logger import audit_log

auth_bp = Blueprint('auth_api', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()

    if not full_name:
        return jsonify({'success': False, 'message': 'Full name is required.'}), 400

    if not validate_email(email):
        return jsonify({'success': False, 'message': 'Please enter a valid email address.'}), 400

    valid_pw, pw_err = validate_password(password)
    if not valid_pw:
        return jsonify({'success': False, 'message': pw_err}), 400

    # Check if email is already taken
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'An account with this email already exists.'}), 409

    new_user = User(
        full_name=full_name,
        email=email,
        role='customer',  # Public registrations are strictly customer role
        phone=phone,
        address=address
    )
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    audit_log("USER_REGISTER", user_id=new_user.id, details={'email': email, 'role': 'customer'})

    # Create JWT token
    token = create_access_token(identity=str(new_user.id))
    session['user_id'] = new_user.id
    session['user_role'] = new_user.role

    return jsonify({
        'success': True,
        'message': 'Registration successful! Welcome to the platform.',
        'token': token,
        'user': new_user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        audit_log("LOGIN_FAILED", details={'email': email})
        return jsonify({'success': False, 'message': 'Invalid email or password.'}), 401

    # Generate JWT token
    token = create_access_token(identity=str(user.id))
    session['user_id'] = user.id
    session['user_role'] = user.role

    audit_log("LOGIN_SUCCESS", user_id=user.id, details={'role': user.role})

    # Determine default redirect path based on role
    redirect_map = {
        'admin': '/admin/dashboard',
        'employee': '/employee/dashboard',
        'customer': '/'
    }

    return jsonify({
        'success': True,
        'message': f'Welcome back, {user.full_name}!',
        'token': token,
        'user': user.to_dict(),
        'redirect': redirect_map.get(user.role, '/')
    }), 200


@auth_bp.route('/me', methods=['GET'])
def get_me():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'authenticated': False}), 200
    return jsonify({
        'success': True,
        'authenticated': True,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/profile', methods=['PUT'])
@token_or_session_required
def update_profile():
    user = get_current_user()
    data = request.get_json() or {}

    full_name = data.get('full_name')
    phone = data.get('phone')
    address = data.get('address')
    new_password = data.get('new_password')

    if full_name:
        user.full_name = full_name.strip()
    if phone is not None:
        user.phone = phone.strip()
    if address is not None:
        user.address = address.strip()

    if new_password:
        valid_pw, pw_err = validate_password(new_password)
        if not valid_pw:
            return jsonify({'success': False, 'message': pw_err}), 400
        user.set_password(new_password)

    db.session.commit()
    audit_log("PROFILE_UPDATED", user_id=user.id)

    return jsonify({
        'success': True,
        'message': 'Profile updated successfully.',
        'user': user.to_dict()
    }), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    user = get_current_user()
    if user:
        audit_log("LOGOUT", user_id=user.id)
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully.'}), 200

