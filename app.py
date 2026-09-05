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

    # Init Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access DentiFlow.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

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
        return {
            'app_name': 'DentiFlow',
            'app_tagline': 'Smarter Clinics. Happier Patients.',
            'version': '2.4.0-PRO',
            'patient_record_id': patient.id if patient else None
        }

    # Health Check API
    @app.route('/api/health', methods=['GET'])
    def health_check():
        try:
            db.session.execute(db.text('SELECT 1'))
            return jsonify({
                "status": "ok",
                "database": "mysql",
                "database_connected": True
            })
        except Exception as e:
            app.logger.exception('Database health check failed')
            return jsonify({
                "status": "error",
                "database": "mysql",
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
    @app.errorhandler(404)
    def page_not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({'status': 'error', 'message': 'The requested API resource was not found.'}), 404
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.exception('Unhandled server error', exc_info=e)
        if request.path.startswith('/api/'):
            return jsonify({'status': 'error', 'message': 'The server could not complete that request.'}), 500
        return render_template('500.html'), 500

    return app


app = create_app()

if __name__ == '__main__':
    print("[DentiFlow] Dental Clinic Management System running at http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', 5000)), debug=app.config['DEBUG'])
