from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, AuditLog, Branch, User

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
@login_required
def index():
    branches = Branch.query.all()
    audit_logs = AuditLog.query.order_by(AuditLog.id.desc()).limit(20).all()
    users = User.query.all()
    return render_template('settings.html', branches=branches, audit_logs=audit_logs, users=users)

@settings_bp.route('/api/settings/audit-logs')
@login_required
def get_audit_logs():
    logs = AuditLog.query.order_by(AuditLog.id.desc()).limit(50).all()
    return jsonify({'audit_logs': [l.to_dict() for l in logs]})

@settings_bp.route('/api/settings/reset-demo', methods=['POST'])
@login_required
def reset_demo():
    if current_user.role != 'admin':
        return jsonify({'status': 'error', 'message': 'Only an administrator can reset demo data.'}), 403
    from seed import seed_database
    try:
        seed_database(reset=True)
    except RuntimeError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    return jsonify({'status': 'success', 'message': 'Demo database reset completed.'})
