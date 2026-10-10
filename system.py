import os
import time
import platform
import psutil
from flask import Blueprint, jsonify, current_app
from sqlalchemy import text
from app.extensions import db
from app.utils.auth import role_required

system_bp = Blueprint('system_api', __name__, url_prefix='/api/system')

START_TIME = time.time()

@system_bp.route('/stats', methods=['GET'])
@role_required('admin')
def get_system_stats():
    """
    Operating Systems Concept Demonstration:
    Collects real-time OS metrics via psutil:
    1. Process Management: Active PID, parent PID, process status, CPU & memory consumption.
    2. Concurrency & Threads: Active thread count for the server process.
    3. Memory Management: Total, available, percent used, and process Resident Set Size (RSS).
    4. Database Resource Management: Connection pool status & DB query ping response time.
    """
    process = psutil.Process(os.getpid())
    current_time = time.time()
    uptime_seconds = int(current_time - START_TIME)
    uptime_formatted = f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m {uptime_seconds % 60}s"

    # CPU Telemetry
    cpu_percent = psutil.cpu_percent(interval=None)
    cpu_cores = psutil.cpu_count(logical=True)
    cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)

    # Memory Telemetry
    mem = psutil.virtual_memory()
    proc_mem = process.memory_info()

    # Thread / Concurrency Telemetry
    threads = process.threads()
    thread_count = len(threads)

    # Disk Telemetry
    try:
        disk_path = os.path.splitdrive(os.getcwd())[0] + os.sep if os.name == 'nt' else '/'
        disk = psutil.disk_usage(disk_path)
    except Exception:
        disk = psutil.disk_usage(os.getcwd())

    # Database Connection Pool Telemetry
    db_status = 'Disconnected'
    db_latency_ms = None
    try:
        t0 = time.time()
        db.session.execute(text("SELECT 1")).scalar()
        t1 = time.time()
        db_status = 'Healthy (Connected)'
        db_latency_ms = round((t1 - t0) * 1000, 2)
    except Exception as e:
        db_status = f"Error: {str(e)}"

    pool = getattr(db.engine, 'pool', None)
    pool_info = {
        'pool_size': pool.size() if hasattr(pool, 'size') else 10,
        'checked_in': pool.checkedin() if hasattr(pool, 'checkedin') else 1,
        'checked_out': pool.checkedout() if hasattr(pool, 'checkedout') else 0,
        'overflow': pool.overflow() if hasattr(pool, 'overflow') else 0
    }

    # Tail recent lines from application log file (File Management)
    log_lines = []
    log_file = current_app.config.get('LOG_FILE')
    if log_file and os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                log_lines = f.readlines()[-40:]
        except Exception:
            log_lines = ["Could not read log file."]

    return jsonify({
        'success': True,
        'os_info': {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'architecture': platform.machine(),
            'python_version': platform.python_version()
        },
        'process': {
            'pid': process.pid,
            'name': process.name(),
            'status': process.status(),
            'threads_count': thread_count,
            'cpu_percent': round(process.cpu_percent(interval=None), 1),
            'memory_rss_mb': round(proc_mem.rss / (1024 * 1024), 2),
            'uptime': uptime_formatted,
            'uptime_seconds': uptime_seconds
        },
        'cpu': {
            'total_percent': cpu_percent,
            'core_count': cpu_cores,
            'per_core_percent': cpu_per_core
        },
        'memory': {
            'total_gb': round(mem.total / (1024 ** 3), 2),
            'available_gb': round(mem.available / (1024 ** 3), 2),
            'used_gb': round(mem.used / (1024 ** 3), 2),
            'percent_used': mem.percent
        },
        'disk': {
            'total_gb': round(disk.total / (1024 ** 3), 2),
            'free_gb': round(disk.free / (1024 ** 3), 2),
            'percent_used': disk.percent
        },
        'database': {
            'status': db_status,
            'latency_ms': db_latency_ms,
            'pool': pool_info
        },
        'logs': [line.strip() for line in log_lines]
    }), 200


DEMO_ACCOUNTS_DATA = [
    {
        'role': 'Admin / Executive Owner',
        'email': 'admin@example.com',
        'demo_password': 'Admin@123',
        'access_scope': 'Executive dashboard, catalog administration, supplier procurement, and financial reporting.'
    },
    {
        'role': 'Warehouse Staff / Employee',
        'email': 'employee@example.com',
        'demo_password': 'Employee@123',
        'access_scope': 'Warehouse inventory adjustments, stock alerts resolution, fulfillment queue, and staff messaging.'
    },
    {
        'role': 'E-Commerce Customer',
        'email': 'customer@example.com',
        'demo_password': 'Customer@123',
        'access_scope': 'Storefront catalog, shopping cart, checkout, order tracking, and profile management.'
    }
]

@system_bp.route('/demo-accounts', methods=['GET'])
@role_required('admin')
def get_system_demo_accounts():
    """
    Security Gate: Provides demo account information exclusively to authenticated Administrators.
    Returns HTTP 401 if unauthenticated, HTTP 403 for Customer or Employee roles.
    """
    return jsonify({
        'success': True,
        'accounts': DEMO_ACCOUNTS_DATA
    }), 200

# Admin API Blueprint for /api/admin/*
admin_bp = Blueprint('admin_api', __name__, url_prefix='/api/admin')

@admin_bp.route('/demo-accounts', methods=['GET'])
@role_required('admin')
def get_admin_demo_accounts():
    """
    Admin-only demo credentials endpoint.
    Returns HTTP 401 if unauthenticated, HTTP 403 for Customer or Employee roles.
    """
    return jsonify({
        'success': True,
        'accounts': DEMO_ACCOUNTS_DATA
    }), 200
