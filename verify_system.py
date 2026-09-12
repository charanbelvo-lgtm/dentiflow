import requests

BASE_URL = 'http://127.0.0.1:5000'
results = []

print('=== 1. VERIFYING ALL ROUTES & ROLES ===')
# Public routes
for path in ['/', '/login', '/register', '/book', '/portal']:
    r = requests.get(BASE_URL + path)
    status = 'PASS' if r.status_code == 200 else 'FAIL'
    results.append((path, r.status_code, status))
    print(f'  [PUBLIC]  {path:20} -> Status {r.status_code} [{status}]')

# Doctor session routes
s_doc = requests.Session()
s_doc.get(BASE_URL + '/demo-login/doctor')
doc_routes = [
    '/dashboard', '/appointments', '/patients', '/clinical',
    '/dental-chart', '/treatment-plans', '/billing', '/inventory',
    '/reports', '/staff'
]
for path in doc_routes:
    r = s_doc.get(BASE_URL + path)
    status = 'PASS' if r.status_code == 200 else 'FAIL'
    results.append((path, r.status_code, status))
    print(f'  [DOCTOR]  {path:20} -> Status {r.status_code} [{status}]')

# Patient session routes
s_pat = requests.Session()
s_pat.get(BASE_URL + '/demo-login/patient')
pat_routes = ['/dashboard', '/appointments', '/treatment-plans', '/billing']
for path in pat_routes:
    r = s_pat.get(BASE_URL + path)
    status = 'PASS' if r.status_code == 200 else 'FAIL'
    results.append((path, r.status_code, status))
    print(f'  [PATIENT] {path:20} -> Status {r.status_code} [{status}]')

# Admin session routes (Inventory, Stock, Profits)
s_adm = requests.Session()
s_adm.get(BASE_URL + '/demo-login/admin')
adm_routes = ['/admin-dashboard', '/admin', '/inventory', '/billing', '/reports']
for path in adm_routes:
    r = s_adm.get(BASE_URL + path)
    status = 'PASS' if r.status_code == 200 else 'FAIL'
    results.append((path, r.status_code, status))
    print(f'  [ADMIN]   {path:20} -> Status {r.status_code} [{status}]')

print('\n=== 2. VERIFYING DESIGN SYSTEM TOKENS IN RENDERED HTML ===')
dashboard_html = s_doc.get(BASE_URL + '/dashboard').text
patient_dash_html = s_pat.get(BASE_URL + '/dashboard').text

checks = [
    ('Sidebar Shell (.site-shell)', 'class="site-shell"' in dashboard_html),
    ('Sidebar Nav (.sidebar)', 'class="sidebar"' in dashboard_html),
    ('Topbar Header (.topbar)', 'class="topbar"' in dashboard_html),
    ('Hero Banner (.hero)', 'class="hero"' in dashboard_html),
    ('Grid Layout (.grid .grid-4)', 'grid grid-4' in dashboard_html),
    ('Card Component (.card)', 'class="card' in dashboard_html),
    ('Stat Widget (.stat)', 'class="card stat"' in dashboard_html),
    ('Patient Dashboard Hero', 'class="hero"' in patient_dash_html),
    ('Patient 3-Col Grid', 'grid grid-3' in patient_dash_html),
    ('Firebase Config Script', 'window.FIREBASE_CONFIG' in dashboard_html),
    ('Firebase Client JS', 'firebase_config.js' in dashboard_html),
    ('Design System CSS', 'style.css' in dashboard_html)
]

all_passed = True
for name, passed in checks:
    status_str = 'PASS' if passed else 'FAIL'
    if not passed: all_passed = False
    print(f'  [TOKEN]   {name:30} -> [{status_str}]')

print('\n=== 3. VERIFICATION SUMMARY ===')
failed_routes = [r for r in results if r[2] != 'PASS']
if not failed_routes and all_passed:
    print(f'  [SUCCESS] All {len(results)} routes and {len(checks)} design tokens verified 100% PASS!')
else:
    print('  [FAIL] Issues detected in routes or tokens.')
