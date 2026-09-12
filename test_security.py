import unittest
import json
from app import create_app
from models import db, User, Patient, AuditLog

class DentiFlowSecurityTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    # -------------------------------------------------------------
    # 1. AUTHENTICATION SECURITY TESTS
    # -------------------------------------------------------------
    def test_01_valid_login_admin(self):
        resp = self.client.post('/login', data={'email': 'admin@gmail.com', 'password': 'admin123'})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue('/dashboard' in resp.headers.get('Location', ''))

    def test_02_valid_login_doctor(self):
        resp = self.client.post('/login', data={'email': 'doctor@gmail.com', 'password': 'doctor123'})
        self.assertEqual(resp.status_code, 302)

    def test_03_receptionist_login_blocked(self):
        resp = self.client.post('/login', data={'email': 'reception@gmail.com', 'password': 'reception123'})
        self.assertEqual(resp.status_code, 403)

    def test_04_valid_login_patient(self):
        resp = self.client.post('/login', data={'email': 'patient@gmail.com', 'password': 'patient123'})
        self.assertEqual(resp.status_code, 302)

    def test_05_invalid_password_rejected(self):
        resp = self.client.post('/login', json={'email': 'doctor@gmail.com', 'password': 'WRONG_PASSWORD'})
        self.assertEqual(resp.status_code, 401)
        data = resp.get_json()
        self.assertEqual(data.get('status'), 'error')

        # Verify no active session created
        dash_resp = self.client.get('/dashboard')
        self.assertEqual(dash_resp.status_code, 302)

    def test_06_nonexistent_user_rejected_and_no_account_created(self):
        email = 'hacker_attacker_fake_user@example.com'
        resp = self.client.post('/login', json={'email': email, 'password': 'password123', 'role': 'doctor'})
        self.assertEqual(resp.status_code, 401)
        
        # Verify account was NOT auto-created
        created = User.query.filter_by(email=email).first()
        self.assertIsNone(created, "Security failure: Non-existent account was auto-created during login!")

    def test_07_empty_credentials_rejected(self):
        resp = self.client.post('/login', json={'email': '', 'password': ''})
        self.assertEqual(resp.status_code, 401)

        resp2 = self.client.post('/login', json={'email': 'notanemail', 'password': 'abc'})
        self.assertEqual(resp2.status_code, 401)

    def test_08_inactive_account_blocked(self):
        # Create an inactive user
        inactive = User.query.filter_by(email='suspended@gmail.com').first()
        if not inactive:
            inactive = User(email='suspended@gmail.com', name='Suspended User', role='patient', is_active=False)
            inactive.set_password('suspended123')
            db.session.add(inactive)
            db.session.commit()
        else:
            inactive.role = 'patient'
            inactive.is_active = False
            db.session.commit()

        resp = self.client.post('/login', json={'email': 'suspended@gmail.com', 'password': 'suspended123'})
        self.assertEqual(resp.status_code, 403)
        data = resp.get_json()
        self.assertIn('inactive', data.get('message', '').lower())

    def test_09_demo_login_endpoint_requires_credentials(self):
        # /demo-login/<role> must NOT create unauthenticated sessions
        resp = self.client.get('/demo-login/admin')
        self.assertEqual(resp.status_code, 302)
        self.assertTrue('/login' in resp.headers.get('Location', ''))

        # Verify no session was created
        dash_resp = self.client.get('/dashboard')
        self.assertEqual(dash_resp.status_code, 302)
        self.assertTrue('/login' in dash_resp.headers.get('Location', ''))

    def test_10_signup_workflow_and_duplicate_prevention(self):
        test_email = 'new_registered_patient_2026@gmail.com'
        existing = User.query.filter_by(email=test_email).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        # Valid signup
        resp = self.client.post('/register', json={
            'name': 'New Registered Patient',
            'email': test_email,
            'password': 'securepassword123',
            'role': 'patient',
            'phone': '+91 99999 88888'
        })
        self.assertEqual(resp.status_code, 201)

        # Duplicate signup must be rejected (409 Conflict)
        dup_resp = self.client.post('/register', json={
            'name': 'New Registered Patient Duplicate',
            'email': test_email,
            'password': 'securepassword123',
            'role': 'patient'
        })
        self.assertEqual(dup_resp.status_code, 409)

        # Verify password is encrypted hash
        user = User.query.filter_by(email=test_email).first()
        self.assertIsNotNone(user)
        self.assertNotEqual(user.password_hash, 'securepassword123')
        self.assertTrue(user.check_password('securepassword123'))

    # -------------------------------------------------------------
    # 2. AUTHORIZATION (RBAC) TESTS
    # -------------------------------------------------------------
    def test_11_unauthenticated_protected_routes_denied(self):
        protected_routes = [
            '/dashboard',
            '/clinical',
            '/chart',
            '/dental-chart',
            '/treatment-plans',
            '/billing',
            '/inventory',
            '/staff',
            '/branches',
            '/reports',
            '/operations',
            '/settings'
        ]
        for route in protected_routes:
            resp = self.client.get(route)
            self.assertIn(resp.status_code, [302, 401], f"Route {route} allowed unauthenticated access!")

    def test_12_doctor_rbac_permitted_and_restricted(self):
        with self.client.session_transaction() as sess:
            pass
        # Login as Doctor
        self.client.post('/login', data={'email': 'doctor@gmail.com', 'password': 'doctor123'})

        # Permitted routes (Clinical access: Doctor can view/manage appointments, patients, clinical notes, dental chart, treatment plans)
        self.assertEqual(self.client.get('/dashboard').status_code, 200)
        self.assertEqual(self.client.get('/clinical').status_code, 200)
        self.assertEqual(self.client.get('/dental-chart').status_code, 200)
        self.assertEqual(self.client.get('/treatment-plans').status_code, 200)
        self.assertEqual(self.client.get('/patients').status_code, 200)
        self.assertEqual(self.client.get('/appointments').status_code, 200)

        # Restricted routes: Doctor must NOT access Billing, Inventory, Reports, Staff, Branches, Settings
        self.assertEqual(self.client.get('/billing').status_code, 403, "Doctor was not forbidden from /billing!")
        self.assertEqual(self.client.get('/inventory').status_code, 403, "Doctor was not forbidden from /inventory!")
        self.assertEqual(self.client.get('/reports').status_code, 403, "Doctor was not forbidden from /reports!")
        self.assertEqual(self.client.get('/staff').status_code, 403, "Doctor was not forbidden from /staff!")
        self.assertEqual(self.client.get('/branches').status_code, 403, "Doctor was not forbidden from /branches!")
        self.assertEqual(self.client.get('/settings').status_code, 403, "Doctor was not forbidden from /settings!")
        self.assertEqual(self.client.get('/api/settings/audit-logs').status_code, 403)
        self.assertEqual(self.client.post('/api/staff/shifts', json={'doctor_id': 1, 'date': '2026-09-12'}).status_code, 403)
        self.assertEqual(self.client.get('/book').status_code, 403, "Doctor was not forbidden from booking!")

    def test_13_receptionist_rbac_decommissioned(self):
        # Login attempt as Receptionist must be rejected with 403
        resp = self.client.post('/login', data={'email': 'reception@gmail.com', 'password': 'reception123'})
        self.assertEqual(resp.status_code, 403, "Receptionist login was not rejected with 403!")

        # Demo login attempt must also be rejected
        resp_demo = self.client.get('/demo-login/reception')
        self.assertEqual(resp_demo.status_code, 403, "Reception demo login was not rejected!")

    def test_14_admin_rbac_full_access(self):
        # Login as Admin
        self.client.post('/login', data={'email': 'admin@gmail.com', 'password': 'admin123'})

        admin_routes = [
            '/dashboard',
            '/patients',
            '/appointments',
            '/clinical',
            '/treatment-plans',
            '/billing',
            '/inventory',
            '/staff',
            '/branches',
            '/reports',
            '/settings',
            '/operations'
        ]
        for route in admin_routes:
            self.assertEqual(self.client.get(route).status_code, 200, f"Admin was denied access to {route}!")

    # -------------------------------------------------------------
    # 3. PATIENT DATA ISOLATION TESTS
    # -------------------------------------------------------------
    def test_15_patient_cross_record_access_denied(self):
        # Login as Patient (Ashwini Goud)
        self.client.post('/login', data={'email': 'budigeashwinigoud@gmail.com', 'password': 'patient123'})

        # Patient can view patient dashboard
        self.assertEqual(self.client.get('/dashboard').status_code, 200)

        # Attempt to access another patient's detail (Patient #1, Aravind) -> 403
        resp = self.client.get('/patients/1')
        self.assertEqual(resp.status_code, 403, "Patient was able to view another patient's records!")

        # Attempt to access clinical / teeth finding of Patient #1 -> 403
        resp2 = self.client.get('/api/patients/1/teeth')
        self.assertEqual(resp2.status_code, 403)

    # -------------------------------------------------------------
    # 4. OPEN REDIRECT VULNERABILITY TESTS
    # -------------------------------------------------------------
    def test_16_open_redirect_prevention(self):
        # External URL in next parameter must be rejected
        resp = self.client.post('/login?next=https://attacker-site.com', data={
            'email': 'admin@gmail.com',
            'password': 'admin123'
        })
        self.assertEqual(resp.status_code, 302)
        location = resp.headers.get('Location', '')
        self.assertFalse('attacker-site.com' in location, "Open redirect vulnerability detected!")
        self.assertTrue(location.endswith('/dashboard') or location == '/dashboard')

        # Logout before testing next redirect
        self.client.get('/logout')

        # Valid relative URL must be honored
        resp_valid = self.client.post('/login?next=/appointments', data={
            'email': 'admin@gmail.com',
            'password': 'admin123'
        })
        self.assertEqual(resp_valid.status_code, 302)
        self.assertTrue(resp_valid.headers.get('Location', '').endswith('/appointments'))

    # -------------------------------------------------------------
    # 5. AUDIT LOGGING VERIFICATION TESTS
    # -------------------------------------------------------------
    def test_17_audit_log_events_recorded(self):
        # Trigger failed login
        self.client.post('/login', json={'email': 'admin@gmail.com', 'password': 'wrong_password_test'})

        # Check that LOGIN_FAILED is in audit_logs
        failed_log = AuditLog.query.filter(AuditLog.action.like('%LOGIN_FAILED%')).order_by(AuditLog.id.desc()).first()
        self.assertIsNotNone(failed_log, "AuditLog did not record LOGIN_FAILED event!")

        # Trigger successful login
        self.client.post('/login', data={'email': 'admin@gmail.com', 'password': 'admin123'})
        success_log = AuditLog.query.filter(AuditLog.action.like('%LOGIN_SUCCESS%')).order_by(AuditLog.id.desc()).first()
        self.assertIsNotNone(success_log, "AuditLog did not record LOGIN_SUCCESS event!")

        # Trigger logout
        self.client.get('/logout')
        logout_log = AuditLog.query.filter(AuditLog.action.like('%LOGOUT%')).order_by(AuditLog.id.desc()).first()
        self.assertIsNotNone(logout_log, "AuditLog did not record LOGOUT event!")

        # Trigger access denied as doctor attempting to access /settings
        self.client.post('/login', data={'email': 'doctor@gmail.com', 'password': 'doctor123'})
        self.client.get('/settings')
        denied_log = AuditLog.query.filter(AuditLog.action.like('%ACCESS_DENIED%')).order_by(AuditLog.id.desc()).first()
        self.assertIsNotNone(denied_log, "AuditLog did not record ACCESS_DENIED event!")

    # -------------------------------------------------------------
    # 6. LOGOUT AND SESSION TERMINATION TESTS
    # -------------------------------------------------------------
    def test_18_logout_destroys_session(self):
        # Login
        self.client.post('/login', data={'email': 'admin@gmail.com', 'password': 'admin123'})
        self.assertEqual(self.client.get('/dashboard').status_code, 200)

        # Logout
        self.client.get('/logout')

        # Protected resource must now be denied
        resp = self.client.get('/dashboard')
        self.assertEqual(resp.status_code, 302)
        self.assertTrue('/login' in resp.headers.get('Location', ''))


if __name__ == '__main__':
    unittest.main()
