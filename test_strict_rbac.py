import unittest
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db, User, Patient, Invoice, Doctor, Appointment

class StrictRBACTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

    # -------------------------------------------------------------
    # 1. UNAUTHENTICATED ACCESS (Expected 302 or 401)
    # -------------------------------------------------------------
    def test_01_unauthenticated_requests(self):
        protected_routes = [
            '/dashboard', '/billing', '/inventory', '/reports',
            '/staff', '/branches', '/settings', '/clinical',
            '/dental-chart', '/treatment-plans'
        ]
        for route in protected_routes:
            resp = self.client.get(route)
            self.assertIn(resp.status_code, [302, 401], f"Unauthenticated access allowed on {route}")

        api_routes = [
            '/api/invoices', '/api/inventory', '/api/reports',
            '/api/staff', '/api/dashboard'
        ]
        for api in api_routes:
            resp = self.client.get(api)
            self.assertIn(resp.status_code, [302, 401], f"Unauthenticated API access allowed on {api}")

    # -------------------------------------------------------------
    # 2. DOCTOR RBAC & HARD SECURITY RESTRICTIONS
    # -------------------------------------------------------------
    def test_02_doctor_clinical_access_permitted(self):
        # Login as Doctor
        self.client.post('/login', data={'email': 'doctor@gmail.com', 'password': 'doctor123'})

        # Permitted Clinical Routes
        self.assertEqual(self.client.get('/dashboard').status_code, 200)
        self.assertEqual(self.client.get('/patients').status_code, 200)
        self.assertEqual(self.client.get('/appointments').status_code, 200)
        self.assertEqual(self.client.get('/clinical').status_code, 200)
        self.assertEqual(self.client.get('/dental-chart').status_code, 200)
        self.assertEqual(self.client.get('/treatment-plans').status_code, 200)
        self.assertEqual(self.client.get('/profile').status_code, 200)

    def test_03_doctor_forbidden_from_financial_modules(self):
        # Login as Doctor
        self.client.post('/login', data={'email': 'doctor@gmail.com', 'password': 'doctor123'})

        # Hard requirements: Billing, payments, invoices, reports MUST return 403 Forbidden
        self.assertEqual(self.client.get('/billing').status_code, 403, "Doctor was not forbidden from /billing!")
        self.assertEqual(self.client.get('/api/invoices').status_code, 403, "Doctor was not forbidden from /api/invoices!")
        self.assertEqual(self.client.get('/api/invoices/1').status_code, 403, "Doctor was not forbidden from /api/invoices/1!")
        self.assertEqual(self.client.post('/api/invoices', json={'patient_id': 1, 'subtotal': 1000}).status_code, 403, "Doctor was not forbidden from POST /api/invoices!")
        self.assertEqual(self.client.post('/api/payments', json={'invoice_id': 1, 'amount': 500}).status_code, 403, "Doctor was not forbidden from /api/payments!")
        self.assertEqual(self.client.get('/invoices/1/print').status_code, 403, "Doctor was not forbidden from /invoices/1/print!")
        self.assertEqual(self.client.get('/receipts/1/print').status_code, 403, "Doctor was not forbidden from /receipts/1/print!")
        self.assertEqual(self.client.get('/reports').status_code, 403, "Doctor was not forbidden from /reports!")
        self.assertEqual(self.client.get('/api/reports').status_code, 403, "Doctor was not forbidden from /api/reports!")
        self.assertEqual(self.client.post('/api/treatment-plans/1/convert-to-invoice').status_code, 403, "Doctor was not forbidden from convert-to-invoice!")

    def test_04_doctor_forbidden_from_inventory_and_admin_modules(self):
        # Login as Doctor
        self.client.post('/login', data={'email': 'doctor@gmail.com', 'password': 'doctor123'})

        # Hard requirements: Inventory, staff, branches, settings MUST return 403 Forbidden
        self.assertEqual(self.client.get('/inventory').status_code, 403, "Doctor was not forbidden from /inventory!")
        self.assertEqual(self.client.get('/api/inventory').status_code, 403, "Doctor was not forbidden from /api/inventory!")
        self.assertEqual(self.client.post('/api/inventory/1/adjust', json={'quantity': 5}).status_code, 403, "Doctor was not forbidden from adjust stock!")
        self.assertEqual(self.client.get('/api/inventory/purchase-orders').status_code, 403, "Doctor was not forbidden from purchase orders!")
        self.assertEqual(self.client.get('/staff').status_code, 403, "Doctor was not forbidden from /staff!")
        self.assertEqual(self.client.get('/doctor-profile/1').status_code, 403, "Doctor was not forbidden from /doctor-profile/1!")
        self.assertEqual(self.client.get('/api/staff').status_code, 403, "Doctor was not forbidden from /api/staff!")
        self.assertEqual(self.client.get('/branches').status_code, 403, "Doctor was not forbidden from /branches!")
        self.assertEqual(self.client.get('/settings').status_code, 403, "Doctor was not forbidden from /settings!")

    def test_05_doctor_data_level_security(self):
        # Login as Doctor
        self.client.post('/login', data={'email': 'doctor@gmail.com', 'password': 'doctor123'})

        # 1. Patient detail API must NOT leak invoices or invoice timeline events
        resp = self.client.get('/api/patients/1')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)

        # Invoices must be empty
        self.assertEqual(data.get('invoices'), [], "Doctor received patient invoices in API response!")
        
        # Timeline events must not contain invoices
        for ev in data.get('timeline', []):
            self.assertNotEqual(ev.get('type'), 'invoice', "Doctor received invoice timeline event in patient detail!")

        # Outstanding balance must not be leaked to Doctor
        pat = data.get('patient', {})
        self.assertIsNone(pat.get('outstanding_balance'), "Doctor received patient outstanding balance!")
        self.assertIsNone(pat.get('total_spent'), "Doctor received patient total spent!")

        # 2. Dashboard API must NOT leak revenue or inventory alerts to doctor
        resp_dash = self.client.get('/api/dashboard')
        self.assertEqual(resp_dash.status_code, 200)
        dash_data = json.loads(resp_dash.data)

        # No today_revenue in KPIs
        self.assertNotIn('today_revenue', dash_data.get('kpis', {}), "Doctor received today_revenue in dashboard KPIs!")
        self.assertNotIn('today_revenue_change', dash_data.get('kpis', {}), "Doctor received today_revenue_change in dashboard KPIs!")

        # No inventory alerts in alerts list
        for al in dash_data.get('alerts', []):
            self.assertNotEqual(al.get('category'), 'Inventory', "Doctor received Inventory alert in dashboard!")

        # No revenue_trend or revenue_by_method in charts
        self.assertNotIn('revenue_trend', dash_data.get('charts', {}), "Doctor received revenue_trend chart in dashboard!")
        self.assertNotIn('revenue_by_method', dash_data.get('charts', {}), "Doctor received revenue_by_method chart in dashboard!")

    # -------------------------------------------------------------
    # 3. ADMIN ACCESS (Full Authority)
    # -------------------------------------------------------------
    def test_06_admin_full_access(self):
        # Login as Admin
        self.client.post('/login', data={'email': 'admin@gmail.com', 'password': 'admin123'})

        # Admin can access all financial and inventory modules
        self.assertEqual(self.client.get('/dashboard').status_code, 200)
        self.assertEqual(self.client.get('/billing').status_code, 200)
        self.assertEqual(self.client.get('/api/invoices').status_code, 200)
        self.assertEqual(self.client.get('/inventory').status_code, 200)
        self.assertEqual(self.client.get('/api/inventory').status_code, 200)
        self.assertEqual(self.client.get('/reports').status_code, 200)
        self.assertEqual(self.client.get('/api/reports').status_code, 200)
        self.assertEqual(self.client.get('/staff').status_code, 200)
        self.assertEqual(self.client.get('/branches').status_code, 200)
        self.assertEqual(self.client.get('/settings').status_code, 200)

        # Admin dashboard includes revenue KPI
        resp_dash = self.client.get('/api/dashboard')
        dash_data = json.loads(resp_dash.data)
        self.assertIn('today_revenue', dash_data.get('kpis', {}), "Admin dashboard did not include today_revenue!")

    # -------------------------------------------------------------
    # 4. PATIENT ACCESS (Restricted to Own Data)
    # -------------------------------------------------------------
    def test_07_patient_access_boundaries(self):
        # Login as Patient
        self.client.post('/login', data={'email': 'patient@gmail.com', 'password': 'patient123'})

        # Patient can view dashboard, appointments, and booking
        self.assertEqual(self.client.get('/dashboard').status_code, 200)
        self.assertEqual(self.client.get('/appointments').status_code, 200)
        self.assertEqual(self.client.get('/book').status_code, 200)

        # Patient MUST NOT access Doctor or Admin modules
        self.assertEqual(self.client.get('/billing').status_code, 403)
        self.assertEqual(self.client.get('/inventory').status_code, 403)
        self.assertEqual(self.client.get('/reports').status_code, 403)
        self.assertEqual(self.client.get('/staff').status_code, 403)
        self.assertEqual(self.client.get('/branches').status_code, 403)
        self.assertEqual(self.client.get('/settings').status_code, 403)
        self.assertEqual(self.client.get('/clinical').status_code, 403)
        self.assertEqual(self.client.get('/dental-chart').status_code, 403)

    # -------------------------------------------------------------
    # 5. RECEPTIONIST ROLE REMOVED (Decommissioned)
    # -------------------------------------------------------------
    def test_08_receptionist_completely_blocked(self):
        # Attempt login with receptionist credentials
        resp = self.client.post('/login', data={'email': 'reception@gmail.com', 'password': 'reception123'})
        self.assertEqual(resp.status_code, 403, "Receptionist login was not blocked with 403!")

        # Attempt demo login for reception
        resp_demo = self.client.get('/demo-login/reception')
        self.assertEqual(resp_demo.status_code, 403, "Reception demo login was not blocked!")

if __name__ == '__main__':
    unittest.main()
