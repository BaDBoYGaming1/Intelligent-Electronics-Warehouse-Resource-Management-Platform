from flask import Blueprint, render_template, request, redirect, url_for
from app.utils.auth import get_current_user, view_login_required, view_role_required

views_bp = Blueprint('views', __name__)

# ==========================================
# Public E-Commerce Website Routes
# ==========================================

@views_bp.route('/')
def home():
    return render_template('index.html')

@views_bp.route('/products')
def products():
    return render_template('products.html')

@views_bp.route('/product')
def product_detail():
    return render_template('product.html')

@views_bp.route('/cart')
def cart():
    return render_template('cart.html')

@views_bp.route('/login')
def login():
    # If already logged in, redirect to appropriate role portal
    user = get_current_user()
    if user:
        if user.role == 'admin':
            return redirect(url_for('views.admin_dashboard'))
        elif user.role == 'employee':
            return redirect(url_for('views.employee_dashboard'))
        return redirect(url_for('views.home'))
    return render_template('login.html')

@views_bp.route('/register')
def register():
    user = get_current_user()
    if user:
        return redirect(url_for('views.home'))
    return render_template('register.html')

@views_bp.route('/concepts')
def concepts():
    return render_template('concepts.html')


# ==========================================
# Authenticated Customer Account Routes
# ==========================================

@views_bp.route('/checkout')
@view_login_required
def checkout():
    return render_template('checkout.html')

@views_bp.route('/orders')
@view_login_required
def my_orders():
    return render_template('orders.html')

@views_bp.route('/order-detail')
@view_login_required
def order_detail():
    return render_template('order_detail.html')

@views_bp.route('/profile')
@view_login_required
def profile():
    return render_template('profile.html')


# ==========================================
# Employee Warehouse Operations Routes (Employee + Admin)
# ==========================================

@views_bp.route('/employee/dashboard')
@view_role_required('employee', 'admin')
def employee_dashboard():
    return render_template('employee/dashboard.html')

@views_bp.route('/employee/orders')
@view_role_required('employee', 'admin')
def employee_orders():
    return render_template('employee/orders.html')

@views_bp.route('/employee/inventory')
@view_role_required('employee', 'admin')
def employee_inventory():
    return render_template('employee/inventory.html')

@views_bp.route('/employee/alerts')
@view_role_required('employee', 'admin')
def employee_alerts():
    return render_template('employee/alerts.html')

@views_bp.route('/employee/messages')
@view_role_required('employee', 'admin')
def employee_messages():
    return render_template('employee/messages.html')


# ==========================================
# Admin / Owner Operations Routes (Admin Only)
# ==========================================

@views_bp.route('/admin/dashboard')
@view_role_required('admin')
def admin_dashboard():
    return render_template('admin/dashboard.html')

@views_bp.route('/admin/products')
@view_role_required('admin')
def admin_products():
    return render_template('admin/products.html')

@views_bp.route('/admin/inventory')
@view_role_required('admin')
def admin_inventory():
    return render_template('admin/inventory.html')

@views_bp.route('/admin/orders')
@view_role_required('admin')
def admin_orders():
    return render_template('admin/orders.html')

@views_bp.route('/admin/suppliers')
@view_role_required('admin')
def admin_suppliers():
    return render_template('admin/suppliers.html')

@views_bp.route('/admin/purchase-orders')
@view_role_required('admin')
def admin_purchase_orders():
    return render_template('admin/purchase_orders.html')

@views_bp.route('/admin/stock-movements')
@view_role_required('admin')
def admin_stock_movements():
    return render_template('admin/stock_movements.html')

@views_bp.route('/admin/alerts')
@view_role_required('admin')
def admin_alerts():
    return render_template('admin/alerts.html')

@views_bp.route('/admin/messages')
@view_role_required('admin')
def admin_messages():
    return render_template('admin/messages.html')

@views_bp.route('/admin/recommendations')
@view_role_required('admin')
def admin_recommendations():
    return render_template('admin/recommendations.html')

@views_bp.route('/admin/reports')
@view_role_required('admin')
def admin_reports():
    return render_template('admin/reports.html')

@views_bp.route('/admin/system-monitor')
@view_role_required('admin')
def admin_system_monitor():
    return render_template('admin/system_monitor.html')

@views_bp.route('/admin/architecture')
@view_role_required('admin')
def admin_architecture():
    return render_template('admin/architecture.html')
