from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.alert import Alert
from app.services.alert_service import resolve_alert
from app.utils.auth import role_required, get_current_user

alerts_bp = Blueprint('alerts_api', __name__, url_prefix='/api/alerts')

@alerts_bp.route('', methods=['GET'])
@role_required('admin', 'employee')
def list_alerts():
    status = request.args.get('status', 'ACTIVE')
    query = Alert.query
    if status != 'ALL':
        query = query.filter_by(status=status)
    alerts = query.order_by(Alert.created_at.desc()).all()

    return jsonify({
        'success': True,
        'alerts': [a.to_dict() for a in alerts],
        'active_count': Alert.query.filter_by(status='ACTIVE').count()
    }), 200

@alerts_bp.route('/<int:alert_id>/resolve', methods=['POST'])
@role_required('admin', 'employee')
def handle_resolve_alert(alert_id):
    success = resolve_alert(alert_id)
    if success:
        return jsonify({'success': True, 'message': 'Alert marked as resolved.'}), 200
    return jsonify({'success': False, 'message': 'Alert not found or already resolved.'}), 404

