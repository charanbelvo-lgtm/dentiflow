import os
from flask import Flask, render_template, jsonify, send_from_directory, request
from flask_cors import CORS
from flask_login import LoginManager, current_user
from config import Config
from models import db, User, Patient

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS
    CORS(app)

    # Init DB
    db.init_app(app)

    # Init Firebase Service (Graceful fallback if unconfigured)
    try:
        from firebase_service import init_firebase
        init_firebase(app)
    except Exception as e:
        app.logger.info(f"Firebase init deferred: {e}")

    # Init Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.session_protection = 'strong'
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access DentiFlow.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        try:
            user = User.query.get(int(user_id))
            if user and not getattr(user, 'is_active', True):
                return None
            return user
        except Exception:
            return None

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.patients import patients_bp
    from routes.appointments import appointments_bp
    from routes.queue import queue_bp
    from routes.clinical import clinical_bp
    from routes.treatment_plans import treatment_plans_bp
    from routes.billing import billing_bp
    from routes.inventory import inventory_bp
    from routes.staff import staff_bp
    from routes.branches import branches_bp
    from routes.reports import reports_bp
    from routes.operations import operations_bp
    from routes.public_booking import public_bp
    from routes.settings import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(queue_bp)
    app.register_blueprint(clinical_bp)
    app.register_blueprint(treatment_plans_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(branches_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(operations_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(settings_bp)

    # Jinja Template Filters
    @app.template_filter('currency')
    def format_currency(value):
        try:
            val = float(value)
            return f"₹{val:,.2f}"
        except (ValueError, TypeError):
            return f"₹0.00"

    @app.template_filter('currency_round')
    def format_currency_round(value):
        try:
            val = float(value)
            return f"₹{val:,.0f}"
        except (ValueError, TypeError):
            return f"₹0"

    # Context Processors
    @app.context_processor
    def inject_global_vars():
        patient = Patient.query.filter_by(email=current_user.email).first() if current_user.is_authenticated and current_user.role == 'patient' else None
        firebase_config = {
            'apiKey': app.config.get('FIREBASE_API_KEY', ''),
            'authDomain': app.config.get('FIREBASE_AUTH_DOMAIN', ''),
            'projectId': app.config.get('FIREBASE_PROJECT_ID', ''),
            'storageBucket': app.config.get('FIREBASE_STORAGE_BUCKET', ''),
            'messagingSenderId': app.config.get('FIREBASE_MESSAGING_SENDER_ID', ''),
            'appId': app.config.get('FIREBASE_APP_ID', ''),
            'measurementId': app.config.get('FIREBASE_MEASUREMENT_ID', '')
        }
        return {
            'app_name': 'DentiFlow',
            'app_tagline': 'Smarter Clinics. Happier Patients.',
            'version': '2.4.0-PRO',
            'patient_record_id': patient.id if patient else None,
            'firebase_config': firebase_config,
            'firebase_configured': bool(app.config.get('FIREBASE_PROJECT_ID'))
        }

    # Health Check API
    @app.route('/api/health', methods=['GET'])
    def health_check():
        try:
            db.session.execute(db.text('SELECT 1'))
            db_type = 'mysql' if 'mysql' in str(db.engine.url) else 'sqlite'
            return jsonify({
                "status": "ok",
                "database": db_type,
                "database_connected": True
            })
        except Exception as e:
            app.logger.exception('Database health check failed')
            return jsonify({
                "status": "error",
                "database_connected": False,
                "error": "Database connection is unavailable."
            }), 500

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(app.static_folder, 'favicon.svg', mimetype='image/svg+xml')

    @app.route('/system-guide')
    def system_guide():
        return send_from_directory(os.path.join(app.root_path, 'docs'), 'DentiFlow_System_Guide.html')

    @app.route('/system-guide.pdf')
    def system_guide_pdf():
        return send_from_directory(os.path.join(app.root_path, 'docs'), 'DentiFlow_System_Guide.pdf', mimetype='application/pdf')

    @app.route('/system-guide.docx')
    def system_guide_docx():
        return send_from_directory(os.path.join(app.root_path, 'docs'), 'DentiFlow_System_Guide.docx', mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document', as_attachment=True)

    # Error Handlers
    @app.errorhandler(401)
    def unauthorized(e):
        if request.path.startswith('/api/') or request.is_json:
            return jsonify({'status': 'error', 'message': 'Authentication required.'}), 401
        return redirect(url_for('auth.login', next=request.path if request.method == 'GET' else None))

    @app.errorhandler(403)
    def forbidden(e):
        if request.path.startswith('/api/') or request.is_json:
            return jsonify({'status': 'error', 'message': 'Access forbidden: insufficient permissions.'}), 403
        return render_template('404.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        if request.path.startswith('/api/') or request.is_json:
            return jsonify({'status': 'error', 'message': 'The requested API resource was not found.'}), 404
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.exception('Unhandled server error', exc_info=e)
        if request.path.startswith('/api/') or request.is_json:
            return jsonify({'status': 'error', 'message': 'The server could not complete that request.'}), 500
        return render_template('500.html'), 500

    # Support reverse proxy headers (e.g. Cloudflare Tunnel / ngrok / NGINX)
    try:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    except Exception:
        pass

    return app


app = create_app()

def get_network_ips():
    """Detect LAN IPv4 addresses on active network adapters (Wi-Fi / Ethernet)."""
    ips = []
    try:
        import subprocess
        output = subprocess.check_output('ipconfig', text=True, stderr=subprocess.DEVNULL)
        current_adapter = None
        for line in output.splitlines():
            if line and not line.startswith(' ') and ':' in line:
                current_adapter = line.strip().rstrip(':')
            elif current_adapter and 'IPv4 Address' in line:
                ip = line.split(':')[-1].strip()
                if ip and not ip.startswith('127.'):
                    ips.append((current_adapter, ip))
    except Exception:
        pass

    # Fallback via socket if ipconfig unavailable
    if not ips:
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            sock_ip = s.getsockname()[0]
            s.close()
            if sock_ip and not sock_ip.startswith('127.'):
                ips.append(('Local Network', sock_ip))
        except Exception:
            pass
    return ips


if __name__ == '__main__':
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    adapters = get_network_ips()

    # Prioritize Wi-Fi or Ethernet adapter if available
    preferred_ip = None
    for name, ip in adapters:
        if any(w in name.lower() for w in ['wi-fi', 'wifi', 'wireless', 'ethernet']):
            preferred_ip = ip
            break
    if not preferred_ip and adapters:
        preferred_ip = adapters[-1][1]

    print("\n" + "=" * 64)
    print(" [DentiFlow] Clinic Management System")
    print("=" * 64)
    print(f" * This PC:       http://localhost:{port}")
    if preferred_ip:
        print(f" * Other Devices: http://{preferred_ip}:{port}  (Same Wi-Fi)")
    for name, ip in adapters:
        if ip != preferred_ip and 'warp' not in name.lower():
            print(f" * Alt ({name}): http://{ip}:{port}")
    print("=" * 64)
    print(" [i] To access from ANY device over the internet (cellular/remote):")
    print("     Run: python share_network.py")
    print("=" * 64 + "\n")

    app.run(host=host, port=port, debug=app.config['DEBUG'])
