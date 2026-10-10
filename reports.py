from flask import Blueprint, request, jsonify, Response
from app.services.report_service import get_dashboard_analytics, generate_csv_report
from app.services.recommendation_service import analyze_inventory_recommendations
from app.utils.auth import role_required

reports_bp = Blueprint('reports_api', __name__, url_prefix='/api/reports')

@reports_bp.route('/analytics', methods=['GET'])
@role_required('admin', 'employee')
def get_analytics():
    data = get_dashboard_analytics()
    return jsonify({'success': True, 'analytics': data}), 200

@reports_bp.route('/recommendations', methods=['GET'])
@role_required('admin', 'employee')
def get_recommendations():
    days = request.args.get('days', 30, type=int)
    lead_time = request.args.get('lead_time', 5, type=int)
    recs = analyze_inventory_recommendations(days_window=days, lead_time_days=lead_time)
    return jsonify({
        'success': True,
        'recommendations': recs,
        'total': len(recs),
        'high_risk_count': sum(1 for r in recs if r['risk_level'] in ['CRITICAL', 'HIGH'])
    }), 200

@reports_bp.route('/export/<report_type>', methods=['GET'])
@role_required('admin')
def export_csv(report_type):
    valid_reports = ['sales', 'inventory', 'movements']
    if report_type not in valid_reports:
        return jsonify({'success': False, 'message': f"Invalid report type. Allowed: {', '.join(valid_reports)}"}), 400

    csv_data = generate_csv_report(report_type)
    filename = f"{report_type}_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )

from datetime import datetime

