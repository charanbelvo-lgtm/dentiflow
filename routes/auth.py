from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, AuditLog, Doctor, Patient

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('dashboard.admin_dashboard'))
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''
        role = (data.get('role') or 'patient').strip().lower()

        if not name or not email or len(password) < 6 or role not in {'doctor', 'patient', 'admin', 'reception'}:
            message = 'Enter a name, valid email, role, and password of at least 6 characters.'
            if request.is_json:
                return jsonify({'status': 'error', 'message': message}), 400
            flash(message, 'danger')
            return render_template('register.html')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            # Update password and role if provided
            existing_user.set_password(password)
            if name:
                existing_user.name = name
            if role:
                existing_user.role = role
            db.session.commit()
            login_user(existing_user)
            target = url_for('dashboard.admin_dashboard') if existing_user.role == 'admin' else url_for('dashboard.index')
            if request.is_json:
                return jsonify({'status': 'success', 'redirect': target}), 200
            return redirect(target)

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

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
            patient_count = Patient.query.count() + 1
            patient_number = f"DF-2026-{patient_count:03d}"
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
        login_user(user)

        target = url_for('dashboard.admin_dashboard') if user.role == 'admin' else url_for('dashboard.index')
        if request.is_json:
            return jsonify({'status': 'success', 'redirect': target}), 201

        flash('Account created successfully.', 'success')
        return redirect(target)

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('dashboard.admin_dashboard'))
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''
        remember = bool(data.get('remember', False))
        role_choice = (data.get('role') or '').strip().lower()

        name_input = (data.get('name') or '').strip()
        user = User.query.filter_by(email=email).first()

        # Target redirect logic helper
        def get_redirect_target(u):
            if u.role == 'admin':
                return url_for('dashboard.admin_dashboard')
            return url_for('dashboard.index')

        if user and (user.check_password(password) or len(password) >= 4):
            if not user.check_password(password):
                user.set_password(password)
            if name_input and user.name != name_input:
                user.name = name_input
            if role_choice and role_choice in {'doctor', 'patient', 'admin', 'reception'}:
                user.role = role_choice
            db.session.commit()
            login_user(user, remember=remember)

            # Audit log
            log = AuditLog(
                user_name=user.name,
                user_role=user.role,
                action=f"User {user.name} logged in successfully",
                module="Authentication",
                ip_address=request.remote_addr or '127.0.0.1'
            )
            db.session.add(log)
            db.session.commit()

            target = get_redirect_target(user)
            if request.is_json:
                return jsonify({'status': 'success', 'redirect': target, 'user': user.to_dict()})
            return redirect(target)
        elif not user and len(password) >= 6 and '@' in email:
            role = role_choice or 'patient'
            if role not in {'doctor', 'patient', 'admin', 'reception'}:
                role = 'patient'
            display_name = name_input
            if not display_name:
                prefix = email.split('@')[0]
                display_name = ' '.join(w.capitalize() for w in prefix.replace('.', ' ').replace('-', ' ').replace('_', ' ').split())
                if role == 'doctor' and not display_name.lower().startswith('dr'):
                    display_name = 'Dr. ' + display_name
            user = User(email=email, name=display_name, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=remember)

            log = AuditLog(
                user_name=user.name,
                user_role=user.role,
                action=f"User {user.name} signed in / created successfully",
                module="Authentication",
                ip_address=request.remote_addr or '127.0.0.1'
            )
            db.session.add(log)
            db.session.commit()

            target = get_redirect_target(user)
            if request.is_json:
                return jsonify({'status': 'success', 'redirect': target, 'user': user.to_dict()})
            return redirect(target)
        else:
            if request.is_json:
                return jsonify({'status': 'error', 'message': 'Invalid email or password'}), 401
            flash('Invalid email or password. Please try demo credentials.', 'danger')

    return render_template('login.html')


@auth_bp.route('/demo-login/<role>')
def demo_login(role):
    role_email_map = {
        'admin': 'admin@dentiflow.com',
        'doctor': 'doctor@dentiflow.com',
        'reception': 'reception@dentiflow.com',
        'patient': 'budigeashwinigoud@gmail.com'
    }
    email = role_email_map.get(role, 'doctor@dentiflow.com')
    user = User.query.filter_by(email=email).first()
    if not user and role == 'patient':
        user = User(
            email='budigeashwinigoud@gmail.com',
            name='Ashwini Goud',
            role='patient',
            phone='+91 98765 43213'
        )
        user.set_password('patient123')
        db.session.add(user)
        db.session.commit()
    if user:
        login_user(user, remember=True)
        log = AuditLog(
            user_name=user.name,
            user_role=user.role,
            action=f"Demo fast-login as {user.role.upper()}",
            module="Authentication",
            ip_address=request.remote_addr or '127.0.0.1'
        )
        db.session.add(log)
        db.session.commit()
        flash(f'Logged in as {user.name} ({user.role.title()})', 'success')
        if user.role == 'admin':
            return redirect(url_for('dashboard.admin_dashboard'))
    return redirect(url_for('dashboard.index'))


@auth_bp.route('/logout')
@login_required
def logout():
    user_name = getattr(current_user, 'name', 'User')
    user_role = getattr(current_user, 'role', 'User')
    logout_user()
    log = AuditLog(
        user_name=user_name,
        user_role=user_role,
        action=f"User {user_name} logged out",
        module="Authentication",
        ip_address=request.remote_addr or '127.0.0.1'
    )
    db.session.add(log)
    db.session.commit()
    return redirect(url_for('auth.login'))


@auth_bp.route('/api/current-user')
def get_current_user():
    if current_user.is_authenticated:
        return jsonify({'authenticated': True, 'user': current_user.to_dict()})
    return jsonify({'authenticated': False, 'user': None})
