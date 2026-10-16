import os
import threading
import time
from flask import Flask, jsonify, render_template, request
from config import Config
from app.extensions import db, jwt, cors
from app.utils.logger import setup_logger

def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    )
    app.config.from_object(config_class)

    # Initialize Extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)

    # Setup OS File Logging
    setup_logger(app)

    # Ensure uploads and logs folders exist
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'static/uploads/products'), exist_ok=True)
    os.makedirs(app.config.get('LOG_FOLDER', 'logs'), exist_ok=True)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.products import products_bp
    from app.routes.categories import categories_bp
    from app.routes.orders import orders_bp
    from app.routes.inventory import inventory_bp
    from app.routes.suppliers import suppliers_bp
    from app.routes.purchase_orders import purchase_orders_bp
    from app.routes.alerts import alerts_bp
    from app.routes.messages import messages_bp
    from app.routes.reports import reports_bp
    from app.routes.system import system_bp, admin_bp
    from app.routes.views import views_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(purchase_orders_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(views_bp)

    # Global Error Handlers (JSON for APIs, clean feedback for pages)
    @app.errorhandler(400)
    def bad_request_error(e):
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'message': 'Bad request', 'error': str(e)}), 400
        return render_template('error.html', code=400, message="Bad Request"), 400

    @app.errorhandler(401)
    def unauthorized_error(e):
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'message': 'Authentication required. Please log in.'}), 401
        return render_template('error.html', code=401, message="Unauthorized. Please log in to access this page."), 401

    @app.errorhandler(403)
    def forbidden_error(e):
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'message': 'Access forbidden.'}), 403
        return render_template('error.html', code=403, message="Access Forbidden. You do not have permissions for this resource."), 403

    @app.errorhandler(404)
    def not_found_error(e):
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'message': 'Resource not found.'}), 404
        return render_template('error.html', code=404, message="Page Not Found."), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f"Internal Server Error: {str(e)}")
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'message': 'An internal server error occurred.'}), 500
        return render_template('error.html', code=500, message="An internal server error occurred. Please try again later."), 500

    return app


_worker_lock = threading.Lock()
_worker_started = False

def start_background_inventory_worker(app):
    """
    OS Process & Thread Management Concept:
    Spawns a dedicated daemon thread that executes background tasks without blocking web requests.
    Periodically checks inventory levels and generates low-stock alerts.
    Guarded against duplicate spawns across workers or reloads.
    """
    global _worker_started
    with _worker_lock:
        if _worker_started or getattr(app, '_inventory_worker_started', False):
            return getattr(app, '_inventory_worker_thread', None)
        _worker_started = True
        app._inventory_worker_started = True

    def worker_loop():
        interval = app.config.get('BACKGROUND_WORKER_INTERVAL', 60)
        app.logger.info(f"OS Background Inventory Worker Thread started (Interval: {interval}s).")
        while True:
            time.sleep(interval)
            try:
                with app.app_context():
                    from app.models.product import Product
                    from app.services.alert_service import check_product_stock_alert
                    products = Product.query.filter_by(status='active').all()
                    for p in products:
                        check_product_stock_alert(p.id)
                    db.session.commit()
            except Exception as e:
                app.logger.error(f"Background worker error: {str(e)}")
                try:
                    with app.app_context():
                        db.session.rollback()
                except Exception:
                    pass
            finally:
                try:
                    with app.app_context():
                        db.session.remove()
                except Exception:
                    pass

    worker_thread = threading.Thread(target=worker_loop, daemon=True, name="InventoryMonitorThread")
    worker_thread.start()
    app._inventory_worker_thread = worker_thread
    return worker_thread

