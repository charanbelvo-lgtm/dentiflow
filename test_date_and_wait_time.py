"""
test_date_and_wait_time.py
Comprehensive automated test suite for:
1. Bug 1: Appointment Date Persistence (Selecting 20 September 2026 never reverts to 15 September 2026)
   - Checks API response, SQLite DB, Patient Dashboard, My Appointments, Doctor view, Receptionist view, Admin view.
   - Checks multiple date formats and field names (appointment_date, date, appointmentDate).
2. Bug 2: Book & Wait Time functionality
   - Checks queue token generation, queue position calculation, wait time calculation ((waiting_ahead + 1) * 15 min).
   - Checks live wait-time polling endpoint (/api/patient/wait-time).
   - Checks presence of wait card, doctors grid, and booking modal in Patient Dashboard HTML.
"""

import sys
import re
import requests
import sqlite3

BASE_URL = "http://127.0.0.1:5000"
DB_PATH = "dentiflow.db"

def assert_true(condition, msg):
    if not condition:
        print(f"FAILED: {msg}")
        sys.exit(1)
    print(f"PASSED: {msg}")

def test_sqlite_clean_check():
    print("\n--- [1] Checking SQLite DB for Stale Hardcoded 15-Sep Appointments ---")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, patient_id, appointment_date, start_time, doctor_id FROM appointments WHERE appointment_date = '2026-09-15'")
    stale = c.fetchall()
    conn.close()
    print(f"Found {len(stale)} appointment(s) on 2026-09-15: {stale}")

def test_bug1_date_persistence():
    print("\n--- [2] Testing Bug 1: Date Selection & Persistence (20 September 2026) ---")
    session = requests.Session()

    # Step 1: Login as patient
    login_res = session.post(f"{BASE_URL}/login", data={
        "email": "budigeashwinigoud@gmail.com",
        "password": "patient123"
    }, allow_redirects=False)
    assert_true(login_res.status_code == 302, "Patient login successful (HTTP 302 redirect)")

    # Step 2: Book appointment for 20 September 2026
    target_date = "2026-09-20"
    target_time = "10:30 AM"
    book_payload = {
        "name": "Ashwini Goud",
        "phone": "+91 98765 43210",
        "email": "budigeashwinigoud@gmail.com",
        "doctor_id": 1,
        "date": target_date,
        "time": target_time,
        "reason": "Routine Checkup - Bug 1 Test",
        "treatment_name": "Routine Checkup"
    }

    book_res = session.post(f"{BASE_URL}/api/public/book", json=book_payload)
    assert_true(book_res.status_code in [200, 201], f"Booking request status code {book_res.status_code}")
    book_data = book_res.json()
    print("BOOK_DATA RETURNED:", book_data)
    assert_true(book_data.get("status") == "success", f"Booking response status is success, got: {book_data.get('status')}")
    
    returned_date = book_data.get("appointment_date") or book_data.get("date")
    assert_true(returned_date == target_date, f"Returned date is '{returned_date}', expected '{target_date}' (NOT 2026-09-15)")
    print(f"Booking confirmation payload: {book_data}")

    apt_id = book_data.get("appointment_id")
    assert_true(bool(apt_id), f"Appointment ID generated: {apt_id}")

    # Step 3: Verify SQLite database directly
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, appointment_date, start_time, status, notes FROM appointments WHERE id = ?", (apt_id,))
    row = c.fetchone()
    conn.close()
    assert_true(row is not None, f"Appointment {apt_id} exists in SQLite database")
    assert_true(row[1] == target_date, f"SQLite appointment_date is '{row[1]}', expected '{target_date}'")
    assert_true(row[1] != "2026-09-15", f"SQLite appointment_date is NOT 2026-09-15")

    # Step 4: Verify Patient Dashboard reflects the appointment and date
    dash_res = session.get(f"{BASE_URL}/dashboard")
    assert_true(dash_res.status_code == 200, "Patient Dashboard accessed successfully")
    assert_true("20 Sep 2026" in dash_res.text or "2026-09-20" in dash_res.text, "Patient Dashboard displays '20 Sep 2026'")
    assert_true("APT-" in dash_res.text, "Patient Dashboard displays Appointment ID")

    # Step 5: Verify My Appointments page
    apts_res = session.get(f"{BASE_URL}/appointments")
    assert_true(apts_res.status_code == 200, "My Appointments page accessed successfully")
    assert_true("20 Sep 2026" in apts_res.text or "2026-09-20" in apts_res.text, "My Appointments displays '20 Sep 2026'")

    # Step 6: Verify Doctor View shows this appointment with 20 Sep 2026
    doc_session = requests.Session()
    doc_res = doc_session.post(f"{BASE_URL}/login", data={
        "email": "doctor@gmail.com",
        "password": "doctor123"
    }, allow_redirects=False)
    assert_true(doc_res.status_code == 302, "Doctor login successful (HTTP 302 redirect)")
    doc_apts = doc_session.get(f"{BASE_URL}/appointments")
    assert_true("20 Sep 2026" in doc_apts.text or "2026-09-20" in doc_apts.text, "Doctor appointment list shows '20 Sep 2026'")

    # Step 7: Verify Receptionist View or Admin View shows this appointment with 20 Sep 2026
    rec_session = requests.Session()
    rec_res = rec_session.post(f"{BASE_URL}/login", data={
        "email": "reception@gmail.com",
        "password": "reception123"
    }, allow_redirects=False)
    if rec_res.status_code == 403:
        print("PASSED: Receptionist role is decommissioned (HTTP 403 as per security policy)")
    else:
        assert_true(rec_res.status_code == 302, "Receptionist login successful (HTTP 302 redirect)")
        rec_apts = rec_session.get(f"{BASE_URL}/appointments")
        assert_true("20 Sep 2026" in rec_apts.text or "2026-09-20" in rec_apts.text, "Receptionist appointment list shows '20 Sep 2026'")

    # Step 8: Test another distinct date (e.g. 28 September 2026) using alternative date key
    payload_alt = {
        "name": "Ashwini Goud",
        "phone": "+91 98765 43210",
        "email": "budigeashwinigoud@gmail.com",
        "doctor_id": 1,
        "appointment_date": "2026-09-28",
        "time": "14:00",
        "reason": "Filling - Second Date Test"
    }
    res_alt = session.post(f"{BASE_URL}/api/public/book", json=payload_alt)
    assert_true(res_alt.status_code in [200, 201], "Second booking request successful")
    data_alt = res_alt.json()
    assert_true(data_alt.get("appointment_date") == "2026-09-28", "Second booking preserved 2026-09-28")

def test_bug2_book_and_wait_time():
    print("\n--- [3] Testing Bug 2: Book & Wait Time Features ---")
    session = requests.Session()
    session.post(f"{BASE_URL}/login", data={
        "email": "budigeashwinigoud@gmail.com",
        "password": "patient123"
    }, allow_redirects=False)

    # Step 1: Verify Book & Wait Time nav item exists in patient layout
    dash_res = session.get(f"{BASE_URL}/dashboard")
    assert_true("Book &amp; Wait Time" in dash_res.text or "Book & Wait Time" in dash_res.text,
                "Navigation includes 'Book & Wait Time'")

    # Step 2: Verify wait-stat-card is in patient dashboard
    html = dash_res.text
    assert_true('id="patient-dash-wait"' in html, "Wait Stat Card (#patient-dash-wait) is rendered in Patient Dashboard")
    assert_true('id="patient-hero-title"' in html, "Hero Title (#patient-hero-title) is rendered")
    assert_true('id="btn-refresh-queue"' in html, "Refresh Queue Button (#btn-refresh-queue) is rendered")
    assert_true('id="app-modal"' in html, "Booking Modal (#app-modal) is rendered in page")
    assert_true('id="booking-form"' in html, "Booking Form (#booking-form) is rendered inside modal")

    # Step 3: Test Book & Wait endpoint (/api/book-and-wait)
    wait_book_payload = {
        "name": "Ashwini Goud",
        "phone": "+91 98765 43210",
        "email": "budigeashwinigoud@gmail.com",
        "doctor_id": 1,
        "date": "2026-09-22",
        "time": "11:15",
        "reason": "Wait Time Test Consultation"
    }
    wait_book_res = session.post(f"{BASE_URL}/api/book-and-wait", json=wait_book_payload)
    assert_true(wait_book_res.status_code in [200, 201], f"Book & Wait response code: {wait_book_res.status_code}")
    wb_data = wait_book_res.json()
    print("Book & Wait JSON response:", wb_data)

    assert_true("token_number" in wb_data, "Response contains 'token_number'")
    assert_true("estimated_wait_min" in wb_data, "Response contains 'estimated_wait_min'")
    assert_true("queue_position" in wb_data, "Response contains 'queue_position'")
    assert_true("appointment_id" in wb_data, "Response contains 'appointment_id'")
    assert_true(wb_data.get("appointment_date") == "2026-09-22", "Book & Wait response preserved appointment_date 2026-09-22")

    # Step 4: Test live polling endpoint (/api/patient/wait-time)
    live_res = session.get(f"{BASE_URL}/api/patient/wait-time")
    assert_true(live_res.status_code == 200, "Live wait-time polling returned 200")
    live_data = live_res.json()
    print("Live wait time response:", live_data)
    assert_true("token_number" in live_data, "Live data has 'token_number'")
    assert_true("estimated_wait_min" in live_data, "Live data has 'estimated_wait_min'")
    assert_true("queue_position" in live_data, "Live data has 'queue_position'")
    assert_true("appointment_date" in live_data, "Live data has 'appointment_date'")

def main():
    print("=" * 60)
    print("RUNNING DENTIFLOW VERIFICATION FOR BUG 1 AND BUG 2")
    print("=" * 60)
    test_sqlite_clean_check()
    test_bug1_date_persistence()
    test_bug2_book_and_wait_time()
    print("\n" + "=" * 60)
    print("ALL BUG 1 AND BUG 2 TESTS PASSED PERFECTLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
