import os

templates_dir = r"c:\Users\chara\OneDrive\Desktop\Dental\templates"
os.makedirs(templates_dir, exist_ok=True)

base_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}DentiFlow{% endblock %}</title>
    <!-- Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <!-- FontAwesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/animations.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/responsive.css') }}">
</head>
<body>
    <div id="toast-container"></div>
    {% if current_user.is_authenticated %}
    <div class="app-container">
        <!-- Sidebar -->
        <aside class="app-sidebar" id="app-sidebar">
            <div class="sidebar-header">
                <div class="logo">
                    <i class="fa-solid fa-tooth text-primary"></i> DentiFlow
                </div>
            </div>
            <nav class="sidebar-nav">
                <a href="/dashboard" class="nav-item"><i class="fa-solid fa-chart-line"></i> Dashboard</a>
                <a href="/queue" class="nav-item"><i class="fa-solid fa-users-viewfinder"></i> Queue</a>
                <a href="/appointments" class="nav-item"><i class="fa-solid fa-calendar-check"></i> Appointments</a>
                <a href="/patients" class="nav-item"><i class="fa-solid fa-hospital-user"></i> Patients</a>
                <a href="/clinical" class="nav-item"><i class="fa-solid fa-tooth"></i> Clinical</a>
                <a href="/treatment-plans" class="nav-item"><i class="fa-solid fa-clipboard-list"></i> Treatment Plans</a>
                <a href="/billing" class="nav-item"><i class="fa-solid fa-file-invoice-dollar"></i> Billing</a>
                <a href="/inventory" class="nav-item"><i class="fa-solid fa-boxes-stacked"></i> Inventory</a>
                <a href="/staff" class="nav-item"><i class="fa-solid fa-user-doctor"></i> Staff</a>
                <a href="/reports" class="nav-item"><i class="fa-solid fa-chart-pie"></i> Reports</a>
                <a href="/operations" class="nav-item"><i class="fa-solid fa-cogs"></i> Operations</a>
            </nav>
            <div class="sidebar-footer">
                <a href="/settings" class="nav-item"><i class="fa-solid fa-gear"></i> Settings</a>
                <a href="/logout" class="nav-item text-danger"><i class="fa-solid fa-arrow-right-from-bracket"></i> Logout</a>
            </div>
        </aside>
        <!-- Main Content -->
        <main class="app-main">
            <header class="app-topbar">
                <button id="sidebar-toggle" class="btn btn-icon"><i class="fa-solid fa-bars"></i></button>
                <div class="topbar-search" id="topbar-search-trigger">
                    <i class="fa-solid fa-search"></i>
                    <span>Search (Ctrl+K)</span>
                </div>
                <div class="topbar-actions">
                    <div class="user-profile">
                        <div class="avatar">{{ current_user.name[0] }}</div>
                        <span class="user-name">{{ current_user.name }}</span>
                    </div>
                </div>
            </header>
            <div class="app-content">
                {% block content %}{% endblock %}
            </div>
        </main>
    </div>
    
    <!-- Global Search Modal -->
    <div id="global-search-modal" class="modal-overlay" style="display:none;">
        <div class="modal-content search-modal" style="margin-top: 50px;">
            <div class="search-input-wrapper">
                <i class="fa-solid fa-search"></i>
                <input type="text" id="global-search-input" placeholder="Search patients, appointments, invoices...">
            </div>
            <div id="global-search-results" class="search-results mt-3"></div>
        </div>
    </div>
    {% else %}
        {% block public_content %}{% endblock %}
    {% endif %}

    <!-- Scripts -->
    <script src="{{ url_for('static', filename='js/app.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
"""

simple_template = """{{% extends "base.html" %}}
{{% block title %}}{title} - DentiFlow{{% endblock %}}
{{% block content %}}
<div class="page-header">
    <h1 class="page-title">{title}</h1>
</div>
<div class="page-body" id="app-root">
    <!-- Frontend JS will mount here or we render basic UI -->
    <div class="card p-4 text-center">
        <i class="fa-solid fa-spinner fa-spin fa-3x text-primary mb-3"></i>
        <h3>Loading {title}...</h3>
        <p class="text-muted">Module is being initialized.</p>
    </div>
</div>
{{% endblock %}}
{{% block scripts %}}
<script src="{{{{ url_for('static', filename='js/{js_file}') }}}}"></script>
{{% endblock %}}
"""

templates = {
    'base.html': base_html,
    'landing.html': '{% extends "base.html" %}{% block public_content %}<div class="text-center" style="margin-top:100px;"><h1>Welcome to DentiFlow</h1><a href="/login" class="btn btn-primary">Login</a></div>{% endblock %}',
    'login.html': '{% extends "base.html" %}{% block public_content %}<div class="text-center" style="margin-top:100px;"><h1>Login</h1><form method="POST" action="/login"><input type="email" name="email" value="admin@dentiflow.com"><input type="password" name="password" value="admin123"><button type="submit" class="btn btn-primary">Login</button></form></div>{% endblock %}',
    'dashboard.html': simple_template.format(title="Dashboard", js_file="dashboard.js"),
    'patients.html': simple_template.format(title="Patients", js_file="patients.js"),
    'patient_detail.html': simple_template.format(title="Patient Detail", js_file="patient_detail.js"),
    'appointments.html': simple_template.format(title="Appointments", js_file="appointments.js"),
    'queue.html': simple_template.format(title="Queue Management", js_file="queue.js"),
    'clinical.html': simple_template.format(title="Clinical", js_file="clinical.js"),
    'treatment_plans.html': simple_template.format(title="Treatment Plans", js_file="treatment_plans.js"),
    'billing.html': simple_template.format(title="Billing & Invoices", js_file="billing.js"),
    'inventory.html': simple_template.format(title="Inventory", js_file="inventory.js"),
    'staff.html': simple_template.format(title="Staff Management", js_file="staff.js"),
    'reports.html': simple_template.format(title="Reports", js_file="reports.js"),
    'operations.html': simple_template.format(title="Operations", js_file="operations.js"),
    'settings.html': simple_template.format(title="Settings", js_file="settings.js"),
    'booking.html': '{% extends "base.html" %}{% block public_content %}<h1>Public Booking</h1>{% endblock %}',
    'patient_portal.html': '{% extends "base.html" %}{% block public_content %}<h1>Patient Portal</h1>{% endblock %}',
    'branches.html': simple_template.format(title="Branches", js_file="branches.js"),
    'print_invoice.html': '<h1>Invoice Print</h1>',
    'print_receipt.html': '<h1>Receipt Print</h1>',
    'print_prescription.html': '<h1>Prescription Print</h1>',
    '404.html': '<h1>404 Not Found</h1>',
    '500.html': '<h1>500 Internal Error</h1>'
}

for filename, content in templates.items():
    with open(os.path.join(templates_dir, filename), 'w', encoding='utf-8') as f:
        f.write(content)

print("Templates created successfully.")
