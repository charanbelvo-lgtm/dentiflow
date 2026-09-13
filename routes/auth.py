from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Doctor, Patient
from security import log_audit_event, get_safe_redirect_url
from firebase_service import sync_user_to_firestore, sync_patient_to_firestore

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''
        role = (data.get('role') or 'patient').strip().lower()

        if not name or not email or len(password) < 6 or role not in {'doctor', 'patient', 'admin'}:
            message = 'Enter a name, valid email, role, and password of at least 6 characters.'
            if request.is_json:
                return jsonify({'status': 'error', 'message': message}), 400
            flash(message, 'danger')
            return render_template('register.html')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            message = 'An account with that email already exists.'
            if request.is_json:
                return jsonify({'status': 'error', 'message': message}), 409
            flash(message, 'danger')
            return render_template('register.html')

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        patient = None
        if role == 'doctor':
            specialty = data.get('specialization') or 'General Dentistry'
            doctor = Doctor(
                user_id=user.id,
                name=name,
                specialty=specialty,
                email=email,
                phone=data.get('phone')
            )
            db.session.add(doctor)
        elif role == 'patient':
            last_pt = Patient.query.order_by(Patient.id.desc()).first()
            next_pt_num = (last_pt.id + 1) if last_pt else 1
            patient_number = f"DF-2026-{str(next_pt_num).zfill(3)}"
            while Patient.query.filter_by(patient_id=patient_number).first():
                next_pt_num += 1
                patient_number = f"DF-2026-{str(next_pt_num).zfill(3)}"

            patient = Patient(
                patient_id=patient_number,
                name=name,
                age=int(data.get('age') or 30),
                gender=data.get('gender') or 'Other',
                phone=data.get('phone') or 'Not provided',
                email=email
            )
            db.session.add(patient)

        db.session.commit()

        # Cloud Firestore Sync
        sync_user_to_firestore(user.to_dict())
        if patient:
            sync_patient_to_firestore(patient.to_dict())

        log_audit_event(
            action=f"User account created for {user.name} ({user.email}) with role '{user.role}'",
            module="Authentication",
            user_name=user.name,
            user_role=user.role
        )

        if request.is_json:
            return jsonify({'status': 'success', 'redirect': url_for('auth.login')}), 201

        flash('Account created. You can now sign in.', 'success')
        return redirect(url_for('auth.login'))

    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''
        remember = bool(data.get('remember', False))

        # Reject empty or malformed credentials immediately
        if not email or not password or '@' not in email:
            log_audit_event(
                action="LOGIN_FAILED: Malformed or missing credentials submitted",
                module="Authentication",
                user_name="Anonymous",
                user_role="guest"
            )
            if request.is_json:
                return jsonify({'status': 'error', 'message': 'Invalid email or password.'}), 401
            flash('Invalid email or password.', 'danger')
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()

        # Reject non-existent user with generic message (no user enumeration)
        if not user:
            log_audit_event(
                action=f"LOGIN_FAILED: Non-existent account login attempt for '{email}'",
                module="Authentication",
                user_name="Anonymous",
                user_role="guest"
            )
            if request.is_json:
                return jsonify({'status': 'error', 'message': 'Invalid email or password.'}), 401
            flash('Invalid email or password.', 'danger')
            return render_template('login.html')

        # Check if account is active
        if not getattr(user, 'is_active', True):
            log_audit_event(
                action=f"LOGIN_BLOCKED: Inactive account login attempt for '{user.email}'",
                module="Authentication",
                user_name=user.name,
                user_role=user.role
            )
            if request.is_json:
                return jsonify({'status': 'error', 'message': 'Account is inactive. Please contact your administrator.'}), 403
            flash('Account is inactive. Please contact your administrator.', 'danger')
            return render_template('login.html'), 403

        # Verify password hash
        if not user.check_password(password):
            log_audit_event(
                action=f"LOGIN_FAILED: Incorrect password attempt for user '{user.email}'",
                module="Authentication",
                user_name=user.name,
                user_role=user.role
            )
            if request.is_json:
                return jsonify({'status': 'error', 'message': 'Invalid email or password.'}), 401
            flash('Invalid email or password.', 'danger')
            return render_template('login.html')

        # Successful authentication: establish session
        login_user(user, remember=remember)

        log_audit_event(
            action=f"LOGIN_SUCCESS: User '{user.name}' ({user.role}) logged in successfully",
            module="Authentication",
            user_name=user.name,
            user_role=user.role
        )

        target_redirect = request.args.get('next')
        if not target_redirect and isinstance(data, dict):
            target_redirect = data.get('next')
        safe_url = get_safe_redirect_url(target_redirect, default=url_for('dashboard.index'))

        if request.is_json:
            return jsonify({'status': 'success', 'redirect': safe_url, 'user': user.to_dict()})
        return redirect(safe_url)

    if current_user.is_authenticated:
        if request.args.get('switch') or request.args.get('role'):
            logout_user()
        else:
            return redirect(url_for('dashboard.index'))

    return render_template('login.html')


@auth_bp.route('/demo-login/<role>')
def demo_login(role):
    """
    Demo login endpoint: Automatically fast-logs into requested role for instant testing.
    """
    normalized_role = (role or '').strip().lower()
    role_email_map = {
        'admin': 'admin@dentiflow.com',
        'doctor': 'doctor@dentiflow.com',
        'reception': 'reception@dentiflow.com',
        'receptionist': 'reception@dentiflow.com',
        'patient': 'budigeashwinigoud@gmail.com'
    }
    email = role_email_map.get(normalized_role, 'doctor@dentiflow.com')
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User.query.filter_by(role=normalized_role).first()
    if user:
        login_user(user, remember=True)
        log_audit_event(
            action=f"Demo fast-login as {user.role.upper()}",
            module="Authentication",
            user_name=user.name,
            user_role=user.role
        )
        flash(f'Logged in as {user.name} ({user.role.title()})', 'success')
    return redirect(url_for('dashboard.index'))


@auth_bp.route('/logout')
@login_required
def logout():
    user_name = getattr(current_user, 'name', 'User')
    user_role = getattr(current_user, 'role', 'User')

    log_audit_event(
        action=f"LOGOUT: User '{user_name}' ({user_role}) logged out",
        module="Authentication",
        user_name=user_name,
        user_role=user_role
    )

    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/api/current-user')
def get_current_user():
    if current_user.is_authenticated:
        return jsonify({'authenticated': True, 'user': current_user.to_dict()})
    return jsonify({'authenticated': False, 'user': None})
