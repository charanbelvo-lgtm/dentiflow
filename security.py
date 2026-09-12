from functools import wraps
from urllib.parse import urlsplit
from flask import request, redirect, url_for, jsonify, abort, current_app
from flask_login import current_user
from models import db, AuditLog

# Role constants
ROLE_ADMIN = 'admin'
ROLE_DOCTOR = 'doctor'
ROLE_RECEPTIONIST = 'receptionist'
ROLE_PATIENT = 'patient'

STAFF_ROLES = {ROLE_ADMIN, ROLE_DOCTOR}
CLINICAL_ROLES = {ROLE_ADMIN, ROLE_DOCTOR}
BILLING_ROLES = {ROLE_ADMIN}
ADMIN_ONLY_ROLES = {ROLE_ADMIN}


def normalize_role(role):
    """Normalize role string to standard values."""
    if not role:
        return ''
    r = role.strip().lower()
    if r == 'reception':
        return ROLE_RECEPTIONIST
    return r


def log_audit_event(action, module="Security", details=None, user_name=None, user_role=None, ip_address=None):
    """
    Safely record an audit log entry for security and compliance events.
    Never raises exceptions that would interrupt the main application flow.
    """
    try:
        if not user_name:
            if current_user and current_user.is_authenticated:
                user_name = getattr(current_user, 'name', None) or getattr(current_user, 'email', 'Authenticated User')
            else:
                user_name = 'Anonymous'

        if not user_role:
            if current_user and current_user.is_authenticated:
                user_role = getattr(current_user, 'role', 'user')
            else:
                user_role = 'guest'

        if not ip_address:
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr or '127.0.0.1')
            if ',' in ip_address:
                ip_address = ip_address.split(',')[0].strip()

        log = AuditLog(
            user_name=user_name[:100],
            user_role=normalize_role(user_role)[:50],
            action=action[:255],
            module=module[:50],
            ip_address=ip_address[:45],
            details=details
        )
        db.session.add(log)
        db.session.commit()
    except Exception as exc:
        try:
            db.session.rollback()
        except Exception:
            pass
        if current_app:
            current_app.logger.warning(f"Audit log recording deferred/failed: {exc}")


def get_safe_redirect_url(target, default=None):
    """
    Validate target redirect URL to ensure it is a safe, internal path.
    Prevents open redirect attacks.
    """
    if not default:
        default = url_for('dashboard.index')

    if not target:
        return default

    target = target.strip()
    # Reject absolute URLs or URLs starting with //
    if target.startswith('//') or '\\' in target:
        return default

    parsed = urlsplit(target)
    # Target must not contain host/scheme (must be relative path)
    if parsed.scheme or parsed.netloc:
        return default

    if not target.startswith('/'):
        return default

    return target


def role_required(*allowed_roles):
    """
    Decorator to enforce role-based access control.
    Returns 401 if unauthenticated, 403 if authenticated but unauthorized.
    Records ACCESS_DENIED audit log event on authorization failure.
    """
    normalized_allowed = {normalize_role(r) for r in allowed_roles}

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'status': 'error', 'message': 'Authentication required.'}), 401
                return current_app.login_manager.unauthorized()

            user_role = normalize_role(getattr(current_user, 'role', ''))
            if user_role not in normalized_allowed:
                log_audit_event(
                    action=f"ACCESS_DENIED: {current_user.name} ({user_role}) denied access to {request.path}",
                    module="Authorization",
                    details=f"Method: {request.method}, Path: {request.path}, Required: {', '.join(sorted(normalized_allowed))}"
                )
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'status': 'error', 'message': 'Access forbidden: insufficient permissions.'}), 403
                abort(403)

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn):
    """Restricted to System Administrators only."""
    return role_required(ROLE_ADMIN)(fn)


def doctor_required(fn):
    """Restricted to Doctors only."""
    return role_required(ROLE_DOCTOR)(fn)


def receptionist_required(fn):
    """Receptionist role has been removed. Always returns 403."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        abort(403)
    return wrapper


def staff_required(fn):
    """Restricted to clinic staff (Admin, Doctor)."""
    return role_required(ROLE_ADMIN, ROLE_DOCTOR)(fn)


def clinical_required(fn):
    """Restricted to Clinical practitioners (Admin, Doctor)."""
    return role_required(ROLE_ADMIN, ROLE_DOCTOR)(fn)


def billing_required(fn):
    """Restricted to Billing / Financial Administration (Admin only)."""
    return role_required(ROLE_ADMIN)(fn)


def patient_required(fn):
    """Restricted to Patients only. Rejects staff roles (Doctor, Admin) with 403."""
    return role_required(ROLE_PATIENT)(fn)

