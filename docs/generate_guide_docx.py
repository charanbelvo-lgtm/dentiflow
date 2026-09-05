from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
OUTPUT = DOCS / 'DentiFlow_System_Guide.docx'
BLUE = RGBColor(37, 99, 235)
NAVY = RGBColor(16, 42, 67)
TEAL = RGBColor(20, 184, 166)
MUTED = RGBColor(82, 103, 124)


def shade(cell, fill):
    properties = cell._tc.get_or_add_tcPr()
    element = OxmlElement('w:shd')
    element.set(qn('w:fill'), fill)
    properties.append(element)


def set_cell_text(cell, text, bold=False, color=NAVY, size=9):
    cell.text = ''
    paragraph = cell.paragraphs[0]
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.color.rgb = color
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def heading(document, text, level=1):
    paragraph = document.add_heading(text, level=level)
    for run in paragraph.runs:
        run.font.color.rgb = NAVY if level == 1 else BLUE
    return paragraph


def paragraph(document, text, bold_prefix=None):
    p = document.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    if bold_prefix and text.startswith(bold_prefix):
        p.add_run(bold_prefix).bold = True
        p.add_run(text[len(bold_prefix):])
    else:
        p.add_run(text)
    return p


def flow_table(document, labels):
    table = document.add_table(rows=1, cols=len(labels) * 2 - 1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for index, label in enumerate(labels):
        cell = table.cell(0, index * 2)
        set_cell_text(cell, label, bold=True, color=NAVY, size=8)
        shade(cell, 'FFFFFF')
        if index < len(labels) - 1:
            set_cell_text(table.cell(0, index * 2 + 1), '>', bold=True, color=TEAL, size=14)
    return table


def data_table(document, headers, rows):
    table = document.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'
    for i, header in enumerate(headers):
        set_cell_text(table.cell(0, i), header, bold=True, color=NAVY, size=8)
        shade(table.cell(0, i), 'DBEAFE')
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], value, size=8)
    document.add_paragraph()
    return table


doc = Document()
section = doc.sections[0]
section.top_margin = Inches(0.55)
section.bottom_margin = Inches(0.55)
section.left_margin = Inches(0.65)
section.right_margin = Inches(0.65)

normal = doc.styles['Normal']
normal.font.name = 'Arial'
normal.font.size = Pt(9.5)
normal.font.color.rgb = NAVY

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('DentiFlow')
r.bold = True
r.font.size = Pt(30)
r.font.color.rgb = NAVY
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('System Workflow and Architecture Guide')
r.font.size = Pt(17)
r.font.color.rgb = BLUE
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.add_run('Plain-language reference for developers, designers, clinic staff, QA, and project reviewers.').italic = True

image_table = doc.add_table(rows=1, cols=2)
image_table.alignment = WD_TABLE_ALIGNMENT.CENTER
for cell, filename in zip(image_table.rows[0].cells, ['cartoon-doctor.png', 'cartoon-patient.png']):
    paragraph_cell = cell.paragraphs[0]
    paragraph_cell.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph_cell.add_run()
    run.add_picture(str(ROOT / 'static' / 'img' / filename), width=Inches(1.55))

paragraph(doc, 'Purpose. DentiFlow connects reception, doctors, patients, clinical records, treatment plans, billing, inventory, and follow-ups in one Flask + MySQL application.', 'Purpose.')
paragraph(doc, 'Important. Seeded clinical information is demonstration data and must not be treated as a confirmed diagnosis or used for real patient care.', 'Important.')

heading(doc, '1. What the system does')
paragraph(doc, 'A person enters through the landing page, signs in or creates an account, and is taken to a role-specific workspace. Clinic staff coordinate visits; doctors review patients and record care; patients see only their own care information.')
data_table(doc, ['Role / area', 'Responsibility'], [
    ('Doctor', 'Reviews patients, appointments, dental findings, periodontal notes, prescriptions, treatment plans, and invoices.'),
    ('Patient', 'Views their own dashboard, appointments, records, treatment plan, prescriptions, and bills.'),
    ('Reception / Admin', 'Manages registration, appointments, queue operations, branches, staff, inventory, reports, settings, and billing.'),
    ('MySQL', 'Stores users, patients, doctors, appointments, queue tokens, clinical records, plans, invoices, payments, and audit logs.'),
])

heading(doc, '2. System architecture')
flow_table(doc, ['Browser\nHTML + CSS + JS', 'Flask routes\nPages + JSON APIs', 'SQLAlchemy\nModels + relationships', 'MySQL\nPersistent data'])
paragraph(doc, 'The browser sends page requests and fetch requests. Flask authenticates the session, validates the request, calls SQLAlchemy, and returns HTML or JSON. PyMySQL connects SQLAlchemy to the existing MySQL database. Local cartoon avatars are served from /static/img. Passwords are stored as hashes.')
heading(doc, 'Request lifecycle', 2)
for item in ['User clicks a link or submits a form.', 'Flask matches the URL to a blueprint route.', 'Flask-Login checks the session and role.', 'The route reads or changes SQLAlchemy model objects.', 'SQLAlchemy reads or writes MySQL.', 'Flask returns HTML or JSON.', 'JavaScript renders success, empty, loading, or error states.']:
    doc.add_paragraph(item, style='List Number')

heading(doc, '3. Complete clinic workflow')
flow_table(doc, ['Reception\nCheck in', 'Queue\nCall / start', 'Doctor\nExamine', 'Tooth chart\nRecord'])
flow_table(doc, ['Treatment plan', 'Invoice', 'Payment', 'Follow-up'])
heading(doc, 'Doctor flow: Aravind example', 2)
paragraph(doc, 'Doctor signs in -> Dashboard -> Patients -> Aravind -> Clinical profile -> Dental Chart -> tooth 16 -> clinical finding -> Treatment Plan -> Invoice -> Payment -> Follow-up.')
heading(doc, 'Patient flow', 2)
paragraph(doc, 'Patient signs in -> Patient Dashboard -> next appointment -> My Records -> Dental History -> Treatment Plan -> Prescription -> Bill. Patient navigation does not expose staff, inventory, other patients, or clinic-wide analytics.')

heading(doc, '4. Main route map')
data_table(doc, ['Area', 'Routes', 'Purpose'], [
    ('Landing', '/', 'Public welcome page or authenticated dashboard.'),
    ('Authentication', '/login, /logout, /register', 'Sign in, sign out, and create a doctor/patient account.'),
    ('Dashboard', '/dashboard, /api/dashboard', 'Role-aware dashboard and operational JSON.'),
    ('Patients', '/patients, /patients/<id>', 'Patient directory and clinical profile.'),
    ('Clinical', '/clinical, /api/patients/<id>/teeth', 'Dental chart, perio, prescriptions, voice notes.'),
    ('Operations', '/appointments, /queue, /staff', 'Visits, waiting queue, and care team profiles.'),
    ('Finance', '/treatment-plans, /billing', 'Plans, invoices, receipts, and payments.'),
    ('Health', '/api/health, /favicon.ico', 'MySQL health check and brand icon.'),
])

heading(doc, '5. Data model map')
data_table(doc, ['Model', 'What it stores', 'Connected records'], [
    ('User', 'Email, password hash, role, branch, avatar, login identity.', 'Doctor profile, audit logs.'),
    ('Patient', 'Demographics, contact, balance, alert state.', 'Appointments, findings, prescriptions, plans, invoices, X-rays.'),
    ('Doctor', 'Specialty, experience, branch, avatar, rating.', 'Appointments, patients, shifts.'),
    ('Appointment / QueueToken', 'Visit date, status, procedure, emergency priority, queue state.', 'Patient, doctor, chair.'),
    ('Clinical records', 'ToothFinding, PeriodontalRecord, ClinicalNote, Prescription, XRayImage.', 'Patient and doctor.'),
    ('Finance', 'TreatmentPlan, phases, items, Invoice, Payment, EMIPlan.', 'Patient, doctor, appointment.'),
])

heading(doc, '6. Security and persistence rules')
for item in ['Passwords are hashed with Werkzeug; plain passwords are not stored.', 'MySQL remains the configured database; normal startup does not drop tables.', 'Destructive demo reset requires explicit opt-in.', 'Patient HTML and API detail routes reject another patient record with HTTP 403.', 'API failures return friendly JSON messages instead of raw tracebacks.', 'Profile images are local cartoon SVG assets; clinical X-rays remain separate clinical records.']:
    doc.add_paragraph(item, style='List Bullet')

heading(doc, '7. Team responsibilities')
data_table(doc, ['Team', 'Owns', 'Done means'], [
    ('Frontend', 'Templates, CSS, JavaScript, responsive states.', 'Loading, success, empty, error, and mobile states work.'),
    ('Backend', 'Routes, auth, permissions, JSON contracts.', 'Status codes, validation, and no unauthorized records.'),
    ('Data', 'Models, MySQL persistence, seed data.', 'Changes survive restart; reset is explicit.'),
    ('QA', 'Route, browser, API, responsive checks.', 'Login, dashboard, patient, chart, billing, and health pass.'),
    ('Design', 'Visual language, cartoons, hierarchy, accessibility.', 'No broken images; readable desktop/mobile layouts.'),
])

heading(doc, '8. Run and test')
for item in ['Install: pip install -r requirements.txt.', 'Start: python app.py.', 'Open: http://127.0.0.1:5000/.', 'Health: /api/health should return status ok, database mysql, and database_connected true.', 'Demo doctor: doctor@dentiflow.com / doctor123.']:
    doc.add_paragraph(item, style='List Number')
paragraph(doc, 'Generated for the DentiFlow internship demonstration. Clinical records shown in the prototype are demo data only.')

doc.save(OUTPUT)
print(OUTPUT)
