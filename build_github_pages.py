import os
import re
import shutil
from app import create_app

app = create_app()

DOCS_DIR = os.path.join(os.path.dirname(__file__), 'docs')
os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(os.path.join(DOCS_DIR, 'css'), exist_ok=True)
os.makedirs(os.path.join(DOCS_DIR, 'js'), exist_ok=True)

# 1. Copy CSS & JS
shutil.copy(os.path.join('static', 'css', 'style.css'), os.path.join(DOCS_DIR, 'css', 'style.css'))

for js_file in os.listdir(os.path.join('static', 'js')):
    if js_file.endswith('.js'):
        shutil.copy(os.path.join('static', 'js', js_file), os.path.join(DOCS_DIR, 'js', js_file))

# Ensure .nojekyll
nojekyll_path = os.path.join(DOCS_DIR, '.nojekyll')
if not os.path.exists(nojekyll_path):
    with open(nojekyll_path, 'w') as f:
        f.write('')

# 2. Pages mapping (Flask Route -> docs HTML file)
PAGE_MAP = {
    '/': 'index.html',
    '/login': 'login.html',
    '/dashboard': 'dashboard.html',
    '/queue': 'queue.html',
    '/appointments': 'appointments.html',
    '/patients': 'patients.html',
    '/patients/1': 'patient-detail.html',
    '/clinical': 'clinical.html',
    '/chart': 'dental-chart.html',
    '/treatment-plans': 'treatment-plans.html',
    '/billing': 'billing.html',
    '/inventory': 'inventory.html',
    '/branches': 'branches.html',
    '/reports': 'reports.html',
    '/operations': 'operations.html',
    '/settings': 'settings.html',
    '/staff': 'staff.html',
    '/portal': 'patient-portal.html',
    '/invoices/1/print': 'print-invoice.html',
    '/receipts/1/print': 'print-receipt.html',
    '/prescriptions/1/print': 'print-prescription.html'
}

URL_REPLACEMENTS = [
    (r'/static/css/', r'./css/'),
    (r'/static/js/', r'./js/'),
    (r'/static/', r'./'),
    (r'href="/dashboard"', r'href="./dashboard.html"'),
    (r'href="/queue"', r'href="./queue.html"'),
    (r'href="/appointments"', r'href="./appointments.html"'),
    (r'href="/patients"', r'href="./patients.html"'),
    (r'href="/patients/\d+"', r'href="./patient-detail.html"'),
    (r'href="/clinical"', r'href="./clinical.html"'),
    (r'href="/chart"', r'href="./dental-chart.html"'),
    (r'href="/dental-chart"', r'href="./dental-chart.html"'),
    (r'href="/treatment-plans"', r'href="./treatment-plans.html"'),
    (r'href="/billing"', r'href="./billing.html"'),
    (r'href="/inventory"', r'href="./inventory.html"'),
    (r'href="/branches"', r'href="./branches.html"'),
    (r'href="/reports"', r'href="./reports.html"'),
    (r'href="/operations"', r'href="./operations.html"'),
    (r'href="/settings"', r'href="./settings.html"'),
    (r'href="/staff"', r'href="./staff.html"'),
    (r'href="/portal"', r'href="./patient-portal.html"'),
    (r'href="/login"', r'href="./login.html"'),
    (r'href="/logout"', r'href="./login.html"'),
    (r'href="/register"', r'href="./login.html"'),
    (r'href="/demo-login/doctor"', r'href="./dashboard.html"'),
    (r'href="/demo-login/admin"', r'href="./dashboard.html"'),
    (r'href="/demo-login/reception\w*"', r'href="./dashboard.html"'),
    (r'href="/demo-login/patient"', r'href="./patient-portal.html"'),
    (r'href="/doctor-profile/\d+"', r'href="./staff.html"'),
    (r'href="/invoices/\d+/print"', r'href="./print-invoice.html"'),
    (r'href="/receipts/\d+/print"', r'href="./print-receipt.html"'),
    (r'href="/prescriptions/\d+/print"', r'href="./print-prescription.html"'),
    (r'href="/favicon\.ico"', r'href="./favicon.ico"'),
    (r'href="/"', r'href="./index.html"'),
    (r'href="/book"', r'href="./index.html"'),
]

# Client-side Mock API script for GitHub Pages static hosting
MOCK_API_SCRIPT = """
<script src="./js/mock_api.js"></script>
"""

with app.test_client() as client:
    # 1. Render patient-dashboard separately
    client.get('/demo-login/patient', follow_redirects=True)
    res = client.get('/dashboard')
    if res.status_code == 200:
        html = res.data.decode('utf-8')
        for pattern, repl in URL_REPLACEMENTS:
            html = re.sub(pattern, repl, html)
        if '</head>' in html:
            html = html.replace('</head>', f'{MOCK_API_SCRIPT}</head>')
        with open(os.path.join(DOCS_DIR, 'patient-dashboard.html'), 'w', encoding='utf-8') as f:
            f.write(html)
        print("Generated patient-dashboard.html")

    # 2. Authenticate as doctor to render all clinical & administrative views
    client.get('/demo-login/doctor', follow_redirects=True)
    
    for route, filename in PAGE_MAP.items():
        if route == '/login':
            client.get('/logout', follow_redirects=True)
            res = client.get('/login')
            client.get('/demo-login/doctor', follow_redirects=True)
        elif route == '/':
            client.get('/logout', follow_redirects=True)
            res = client.get('/')
            client.get('/demo-login/doctor', follow_redirects=True)
        else:
            res = client.get(route)

        if res.status_code != 200:
            print(f"Warning: route {route} returned status {res.status_code}")
            continue

        html = res.data.decode('utf-8')

        # Replace URLs
        for pattern, repl in URL_REPLACEMENTS:
            html = re.sub(pattern, repl, html)

        # Inject mock_api.js before </head> or </body>
        if '</head>' in html:
            html = html.replace('</head>', f'{MOCK_API_SCRIPT}</head>')
        elif '</body>' in html:
            html = html.replace('</body>', f'{MOCK_API_SCRIPT}</body>')

        target_path = os.path.join(DOCS_DIR, filename)
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Generated {filename} ({len(html)} bytes)")

print("Docs export complete!")
