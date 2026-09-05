from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, AuditLog, Doctor, Patient

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        role = data.get('role', 'patient').strip().lower()
        if not name or not email or len(password) < 6 or role not in {'doctor', 'patient'}:
            message = 'Enter a name, valid email, role, and password of at least 6 characters.'
            return (jsonify({'status': 'error', 'message': message}), 400) if request.is_json else (flash(message, 'danger') or render_template('register.html'))
        if User.query.filter_by(email=email).first():
            message = 'An account with that email already exists.'
            return (jsonify({'status': 'error', 'message': message}), 409) if request.is_json else (flash(message, 'danger') or render_template('register.html'))
        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        if role == 'doctor':
            db.session.add(Doctor(user_id=user.id, name=name, specialty=data.get('specialization') or 'General Dentistry', email=email, phone=data.get('phone')))
        else:
            patient_number = f"DF-2026-{Patient.query.count() + 1:03d}"
            db.session.add(Patient(patient_id=patient_number, name=name, age=int(data.get('age') or 30), gender=data.get('gender') or 'Other', phone=data.get('phone') or 'Not provided', email=email))
        db.session.commit()
        if request.is_json:
            return jsonify({'status': 'success', 'redirect': url_for('auth.login')}), 201
        flash('Account created. You can now sign in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        # Support JSON and Form submission
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        remember = bool(data.get('remember', False))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            
            # Log audit
            log = AuditLog(
                user_name=user.name,
                user_role=user.role,
                action=f"User {user.name} logged in successfully",
                module="Authentication",
                ip_address=request.remote_addr or '127.0.0.1'
            )
            db.session.add(log)
            db.session.commit()

            if request.is_json:
                return jsonify({'status': 'success', 'redirect': url_for('dashboard.index'), 'user': user.to_dict()})
            return redirect(url_for('dashboard.index'))
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
        'reception': 'reception@dentiflow.com'
    }
    email = role_email_map.get(role, 'doctor@dentiflow.com')
    user = User.query.filter_by(email=email).first()
    if user:
        login_user(user, remember=True)
        # Log audit
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
    return redirect(url_for('dashboard.index'))

@auth_bp.route('/logout')
@login_required
def logout():
    name = current_user.name
    role = current_user.role
    logout_user()
    log = AuditLog(
        user_name=name,
        user_role=role,
        action=f"User {name} logged out",
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
