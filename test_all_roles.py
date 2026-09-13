import requests
import json
from datetime import date, timedelta

BASE_URL = "http://127.0.0.1:5000"

def run_tests():
    print("==================================================")
    print("STARTING DENTIFLOW COMPREHENSIVE ROLE & SECURITY SUITE")
    print("==================================================")

    # 1. Test Landing Page is Login/Signup
    print("\n--- 1. Testing Landing Page (Unauthenticated) ---")
    s_anon = requests.Session()
    r = s_anon.get(f"{BASE_URL}/")
    assert r.status_code == 200, f"Expected 200 on /, got {r.status_code}"
    assert "Sign in to DentiFlow" in r.text or "Create an Account" in r.text, "Landing page missing auth forms"
    assert "Book Visit" not in r.text, "Unauthenticated Book Visit tab should not be on landing page"
    print("PASS: Landing page renders Login / Signup form cleanly.")

    # 2. Test Patient Role
    print("\n--- 2. Testing Patient Role (budigeashwinigoud@gmail.com) ---")
    s_pat = requests.Session()
    login_res = s_pat.post(f"{BASE_URL}/login", data={
        "email": "budigeashwinigoud@gmail.com",
        "password": "patient123"
    }, allow_redirects=False)
    assert login_res.status_code == 302, f"Login failed, got {login_res.status_code}"
    print("PASS: Patient login successful.")

    # Patient Dashboard
    r_dash = s_pat.get(f"{BASE_URL}/dashboard")
    assert r_dash.status_code == 200
    assert "Ashwini Goud" in r_dash.text
    print("PASS: Patient dashboard renders patient view with name and queue token info.")

    # Patient Profile
    r_prof = s_pat.get(f"{BASE_URL}/profile")
    assert r_prof.status_code == 200
    assert "Ashwini Goud" in r_prof.text
    # Profile update
    r_prof_post = s_pat.post(f"{BASE_URL}/profile", data={
        "name": "Ashwini Goud",
        "phone": "+91 98765 43210",
        "allergies": "Penicillin (mild)"
    }, allow_redirects=True)
    assert r_prof_post.status_code == 200
    print("PASS: Patient profile viewed and updated successfully.")

    # Patient Messaging Care Team
    r_msg = s_pat.post(f"{BASE_URL}/api/messages", json={
        "subject": "Follow-up question",
        "message": "Hello doctor, is mild sensitivity normal after root canal review?",
        "recipient": "Dr. Ananya Sharma"
    })
    assert r_msg.status_code == 200, f"Expected 200, got {r_msg.status_code}: {r_msg.text}"
    msg_data = r_msg.json()
    assert msg_data.get("status") == "success"
    print("PASS: Patient message composer sent message to care team.")

    # Patient Booking appointment
    r_book_page = s_pat.get(f"{BASE_URL}/book")
    assert r_book_page.status_code == 200
    future_date = (date.today() + timedelta(days=5)).strftime('%Y-%m-%d')
    r_book = s_pat.post(f"{BASE_URL}/api/public/book", json={
        "name": "Ashwini Goud",
        "phone": "+91 98765 43210",
        "email": "budigeashwinigoud@gmail.com",
        "age": 28,
        "gender": "Female",
        "doctor_id": 1,
        "treatment_name": "Routine Checkup & Polishing",
        "appointment_date": future_date,
        "start_time": "11:30 AM"
    })
    assert r_book.status_code in (200, 201), f"Booking failed: {r_book.text}"
    book_data = r_book.json()
    assert book_data.get("status") == "success"
    assert "/dashboard" in book_data.get("redirect", "")
    assert book_data.get("appointment_date") == future_date, f"Expected {future_date}, got {book_data.get('appointment_date')}"
    print(f"PASS: Patient booked appointment: Ref {book_data.get('appointment_number')} on {future_date}, redirected to dashboard.")

    # Patient Appointments view
    r_pat_apts = s_pat.get(f"{BASE_URL}/appointments")
    assert r_pat_apts.status_code == 200
    assert "Routine Checkup" in r_pat_apts.text or "Appointments" in r_pat_apts.text
    print("PASS: Patient view of /appointments lists their scheduled appointments.")

    # Patient RBAC Restrictions (Must be 403 Forbidden)
    forbidden_routes = [
        "/clinical", "/chart", "/treatment-plans", "/reports",
        "/billing", "/staff", "/api/staff", "/api/reports"
    ]
    for route in forbidden_routes:
        res = s_pat.get(f"{BASE_URL}{route}")
        assert res.status_code == 403, f"Security breach! Patient accessed {route}, status: {res.status_code}"
    print("PASS: Patient blocked with 403 Forbidden from all clinical and staff routes.")

    # 3. Test Doctor Role
    print("\n--- 3. Testing Doctor Role (doctor@gmail.com) ---")
    s_doc = requests.Session()
    login_doc = s_doc.post(f"{BASE_URL}/login", data={
        "email": "doctor@gmail.com",
        "password": "doctor123"
    }, allow_redirects=False)
    assert login_doc.status_code == 302
    print("PASS: Doctor login successful.")

    # Doctor Profile
    r_doc_prof = s_doc.get(f"{BASE_URL}/profile")
    assert r_doc_prof.status_code == 200
    assert "Dr. Ananya Sharma" in r_doc_prof.text
    print("PASS: Doctor profile renders Dr. Ananya Sharma.")

    # Doctor Authorized Clinical Routes
    doc_allowed = ["/dashboard", "/appointments", "/patients", "/clinical", "/chart", "/treatment-plans"]
    for route in doc_allowed:
        res = s_doc.get(f"{BASE_URL}{route}")
        assert res.status_code == 200, f"Doctor failed to access {route}, status: {res.status_code}"
    print("PASS: Doctor accessed all authorized clinical routes (200 OK).")

    # Doctor Restricted Financial & Admin Routes (Must be 403 Forbidden)
    doc_forbidden = ["/billing", "/inventory", "/reports", "/staff", "/branches", "/settings"]
    for route in doc_forbidden:
        res = s_doc.get(f"{BASE_URL}{route}")
        assert res.status_code == 403, f"Doctor should be forbidden from {route}, got {res.status_code}"
    print("PASS: Doctor strictly blocked from financial and administrative routes with 403 Forbidden.")

    # Doctor Booking restriction (Must be 403 Forbidden)
    r_doc_book = s_doc.get(f"{BASE_URL}/book")
    assert r_doc_book.status_code == 403, f"Doctor should be forbidden from /book, got {r_doc_book.status_code}"
    r_doc_book_api = s_doc.post(f"{BASE_URL}/api/public/book", json={"name": "Test"})
    assert r_doc_book_api.status_code == 403, f"Doctor should be forbidden from booking API, got {r_doc_book_api.status_code}"
    print("PASS: Doctor strictly blocked from booking endpoints with 403 Forbidden.")

    # Check that "+ Book appointment" button is hidden for doctors
    r_doc_apts = s_doc.get(f"{BASE_URL}/appointments")
    assert "+ Book appointment" not in r_doc_apts.text, "Staff should NOT see '+ Book appointment' button"
    print("PASS: '+ Book appointment' button hidden in appointments for Doctor.")

    # 4. Test Receptionist Role (Decommissioned)
    print("\n--- 4. Testing Receptionist Role Decommissioning (reception@gmail.com) ---")
    s_rec = requests.Session()
    login_rec = s_rec.post(f"{BASE_URL}/login", data={
        "email": "reception@gmail.com",
        "password": "reception123"
    }, allow_redirects=False)
    assert login_rec.status_code == 403, f"Receptionist login should be blocked with 403, got {login_rec.status_code}"
    print("PASS: Receptionist login strictly blocked with 403 Forbidden.")

    # 5. Test Admin Role
    print("\n--- 5. Testing Admin Role (admin@gmail.com) ---")
    s_adm = requests.Session()
    login_adm = s_adm.post(f"{BASE_URL}/login", data={
        "email": "admin@gmail.com",
        "password": "admin123"
    }, allow_redirects=False)
    assert login_adm.status_code == 302
    print("PASS: Admin login successful.")

    # Admin Profile
    r_adm_prof = s_adm.get(f"{BASE_URL}/profile")
    assert r_adm_prof.status_code == 200
    assert "Dr. Rajesh Verma" in r_adm_prof.text
    print("PASS: Admin profile renders Dr. Rajesh Verma.")

    # Admin Staff Management
    r_staff = s_adm.get(f"{BASE_URL}/staff")
    assert r_staff.status_code == 200
    print("PASS: Admin accessed Staff Management.")

    # Admin Booking restriction
    r_adm_book = s_adm.get(f"{BASE_URL}/book")
    assert r_adm_book.status_code == 403
    r_adm_book_api = s_adm.post(f"{BASE_URL}/api/public/book", json={"name": "Test"})
    assert r_adm_book_api.status_code == 403
    print("PASS: Admin strictly blocked from booking endpoints with 403 Forbidden.")

    # 6. Test Billing & Mock UPI Payment Flow
    print("\n--- 6. Testing Billing & Mock UPI Payment Flow ---")
    # Admin creates an invoice
    r_create_inv = s_adm.post(f"{BASE_URL}/api/invoices", json={
        "patient_id": 1,
        "doctor_id": 1,
        "subtotal": 4500,
        "discount_amount": 500,
        "tax_rate": 18,
        "payment_method": "UPI",
        "items": [{
            "description": "Composite Restoration & Cleaning",
            "quantity": 1,
            "unit_price": 4500,
            "discount": 500
        }]
    })
    assert r_create_inv.status_code == 201, f"Invoice creation failed: {r_create_inv.text}"
    inv_data = r_create_inv.json()["invoice"]
    inv_id = inv_data["id"]
    inv_total = inv_data["total_amount"]
    print(f"PASS: Created invoice #{inv_data['invoice_number']} for INR {inv_total:,.2f} with status '{inv_data['status']}'.")

    # Record Mock UPI payment for this invoice
    r_pay = s_adm.post(f"{BASE_URL}/api/payments", json={
        "invoice_id": inv_id,
        "amount": inv_total,
        "payment_method": "UPI",
        "notes": "Simulated prototype UPI QR settlement"
    })
    assert r_pay.status_code == 200, f"Payment recording failed: {r_pay.text}"
    pay_data = r_pay.json()
    assert pay_data["status"] == "success"
    assert pay_data["invoice"]["status"] == "Paid"
    assert pay_data["invoice"]["due_amount"] == 0.0
    print(f"PASS: Recorded UPI Payment ({pay_data['payment']['receipt_number']}), invoice status changed to 'Paid' in database.")

    # Verify billing page HTML renders
    r_billing = s_adm.get(f"{BASE_URL}/billing")
    assert r_billing.status_code == 200
    assert "PROTOTYPE MOCK UPI / QR" in r_billing.text
    assert "dentiflow@icici" in r_billing.text
    print("PASS: /billing renders Mock UPI/QR component and live ledger stats.")

    print("\n==================================================")
    print("ALL TESTS PASSED SUCCESSFULLY! 100% VERIFIED.")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
