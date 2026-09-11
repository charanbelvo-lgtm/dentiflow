import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
from app import create_app
from models import db, User, Patient, Doctor, Invoice, Prescription, Payment

app = create_app()

def run_tests():
    with app.test_client() as client:
        print("=== 1. TESTING DEMO LOGINS ===")
        roles = ['doctor', 'admin', 'receptionist', 'patient']
        for r in roles:
            resp = client.get(f'/demo-login/{r}', follow_redirects=True)
            assert resp.status_code == 200, f"Demo login for {r} failed with {resp.status_code}"
            print(f"  ✓ Demo login '{r}' -> Status {resp.status_code} ({resp.request.path})")

        print("\n=== 2. TESTING AUTHENTICATED DOCTOR ACCESS (ALL PAGES) ===")
        client.get('/demo-login/doctor', follow_redirects=True)
        routes = [
            '/',
            '/dashboard',
            '/patients',
            '/patients/1',
            '/appointments',
            '/queue',
            '/clinical',
            '/chart',
            '/treatment-plans',
            '/billing',
            '/invoices/1/print',
            '/receipts/1/print',
            '/prescriptions/1/print',
            '/inventory',
            '/staff',
            '/branches',
            '/reports',
            '/operations',
            '/settings',
        ]
        for path in routes:
            resp = client.get(path)
            assert resp.status_code == 200, f"Route {path} failed with {resp.status_code}"
            print(f"  ✓ Route {path:<26} -> 200 OK")

        print("\n=== 3. TESTING DYNAMIC APIS ===")
        # Test reports API
        r = client.get('/api/reports?timeframe=30d')
        assert r.status_code == 200 and 'revenue_trend' in r.get_json(), "Reports API failed"
        print("  ✓ GET /api/reports?timeframe=30d -> 200 OK")

        # Test teeth API
        r = client.get('/api/patients/1/teeth')
        assert r.status_code == 200 and 'findings' in r.get_json(), "Teeth GET API failed"
        print("  ✓ GET /api/patients/1/teeth -> 200 OK")

        r = client.post('/api/patients/1/teeth', json={
            'tooth_number': 16,
            'status': 'Crown',
            'surfaces': 'MOD',
            'diagnosis': 'Gross coronal loss',
            'recommended_treatment': 'Zirconia Crown',
            'estimated_cost': 8500
        })
        assert r.status_code == 200 and r.get_json()['status'] == 'success', "Teeth POST API failed"
        print("  ✓ POST /api/patients/1/teeth -> 200 OK")

        # Test inventory adjust API
        r = client.post('/api/inventory/1/adjust', json={
            'change_type': 'Add',
            'quantity': 5,
            'reason': 'Test verification restock'
        })
        assert r.status_code == 200 and r.get_json()['status'] == 'success', "Inventory adjust API failed"
        print("  ✓ POST /api/inventory/1/adjust -> 200 OK")

        # Test appointments status API
        r = client.post('/api/appointments/1/status', json={'status': 'Completed'})
        assert r.status_code == 200 and r.get_json()['status'] == 'success', "Appointments status API failed"
        print("  ✓ POST /api/appointments/1/status -> 200 OK")

        # Test clinical voice notes API
        r = client.post('/api/patients/1/voice-notes', json={
            'subjective': 'Verification checkup',
            'objective': 'Gingiva healthy, no pockets',
            'assessment': 'Routine maintenance',
            'plan': 'Recall in 6 months'
        })
        assert r.status_code == 200 and r.get_json()['status'] == 'success', "Clinical notes API failed"
        print("  ✓ POST /api/patients/1/voice-notes -> 200 OK")

        # Test queue API
        r = client.get('/api/queue')
        assert r.status_code == 200, "Queue API failed"
        print("  ✓ GET /api/queue -> 200 OK")

        # Test operations APIs
        r = client.get('/api/operations/lab-orders')
        assert r.status_code == 200, "Lab orders API failed"
        print("  ✓ GET /api/operations/lab-orders -> 200 OK")

        print("\n=== 4. TESTING PATIENT PORTAL ACCESS & RESTRICTIONS ===")
        client.get('/demo-login/patient', follow_redirects=True)
        resp = client.get('/dashboard')
        assert resp.status_code == 200, "Patient dashboard failed"
        print("  ✓ Patient accessing /dashboard (rendered patient_dashboard.html) -> 200 OK")

        resp = client.get('/portal')
        assert resp.status_code == 200, "Patient portal failed"
        print("  ✓ Patient accessing /portal -> 200 OK")

        resp = client.get('/patients/1')
        assert resp.status_code == 200, "Patient accessing own profile failed"
        print("  ✓ Patient accessing own record /patients/1 -> 200 OK")

        # Patient attempting to view another patient's profile should return 403 Forbidden
        resp = client.get('/patients/2')
        assert resp.status_code == 403, f"Patient accessed other patient with code {resp.status_code}"
        print(f"  ✓ Patient accessing /patients/2 -> 403 Forbidden (RBAC Protected!)")

        print("\nALL SYSTEM TESTS PASSED SUCCESSFULLY! 100% HEALTHY.")

if __name__ == '__main__':
    run_tests()
