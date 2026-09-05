from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
PDF_PATH = DOCS / 'DentiFlow_System_Guide.pdf'
BLUE = colors.HexColor('#2563EB')
NAVY = colors.HexColor('#102A43')
TEAL = colors.HexColor('#14B8A6')
PALE = colors.HexColor('#EFF6FF')
MUTED = colors.HexColor('#52677C')

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='CoverTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=28, leading=33, textColor=NAVY, alignment=TA_CENTER, spaceAfter=8))
styles.add(ParagraphStyle(name='Sub', parent=styles['Normal'], fontSize=13, leading=18, textColor=MUTED, alignment=TA_CENTER, spaceAfter=15))
styles.add(ParagraphStyle(name='H2x', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=17, leading=21, textColor=NAVY, spaceBefore=14, spaceAfter=8))
styles.add(ParagraphStyle(name='H3x', parent=styles['Heading3'], fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=BLUE, spaceBefore=8, spaceAfter=4))
styles.add(ParagraphStyle(name='Bodyx', parent=styles['BodyText'], fontSize=9.5, leading=14, textColor=NAVY, spaceAfter=6))
styles.add(ParagraphStyle(name='Smallx', parent=styles['BodyText'], fontSize=8, leading=11, textColor=MUTED))
styles.add(ParagraphStyle(name='Node', parent=styles['BodyText'], fontSize=8.2, leading=10, alignment=TA_CENTER, textColor=NAVY))


def P(text, style='Bodyx'):
    return Paragraph(text, styles[style])


def cartoon(path, width=38*mm):
    drawing = svg2rlg(str(path))
    scale = width / drawing.width
    drawing.width *= scale
    drawing.height *= scale
    drawing.scale(scale, scale)
    return drawing


def box(text, color=BLUE):
    t = Table([[P(text, 'Node')]], colWidths=[35*mm], rowHeights=[18*mm])
    t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.white), ('BOX', (0,0), (-1,-1), 1.5, color), ('VALIGN',(0,0),(-1,-1),'MIDDLE'), ('LEFTPADDING',(0,0),(-1,-1),3), ('RIGHTPADDING',(0,0),(-1,-1),3)]))
    return t


def flow(items):
    cells=[]
    for i, item in enumerate(items):
        cells.append(box(item[0], item[1] if len(item)>1 else BLUE))
        if i < len(items)-1:
            cells.append(P('->', 'H3x'))
    t=Table([cells], colWidths=[35*mm if i%2==0 else 8*mm for i in range(len(cells))])
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(0,0),(-1,-1),'CENTER')]))
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#CBD5E1'))
    canvas.line(15*mm, 12*mm, 195*mm, 12*mm)
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(15*mm, 7*mm, 'DentiFlow System Guide - Demo clinical data only')
    canvas.drawRightString(195*mm, 7*mm, f'Page {doc.page}')
    canvas.restoreState()

story=[]
story += [Spacer(1, 20*mm), P('DentiFlow', 'CoverTitle'), P('System Workflow and Architecture Guide', 'Sub'), P('A plain-language reference for developers, designers, clinic staff, QA, and project reviewers.', 'Sub')]
story += [Table([[cartoon(DOCS.parent/'static/img/cartoon-doctor.svg', 43*mm), cartoon(DOCS.parent/'static/img/cartoon-patient.svg', 43*mm)]], colWidths=[88*mm, 88*mm], style=TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'), ('VALIGN',(0,0),(-1,-1),'MIDDLE')]))]
story += [Spacer(1, 10*mm), flow([('Landing', BLUE), ('Login / Register', TEAL), ('Role Dashboard', BLUE), ('Care action', TEAL)]), Spacer(1, 10*mm)]
story += [P('<b>Purpose.</b> DentiFlow connects reception, doctors, patients, clinical records, treatment plans, billing, inventory, and follow-ups in one Flask + MySQL application.', 'Bodyx'), P('<b>Important.</b> Seeded clinical information is demonstration data and must not be treated as a confirmed diagnosis or used for real patient care.', 'Bodyx'), PageBreak()]

story += [P('1. What the system does', 'H2x'), P('A person enters through the landing page, signs in or creates an account, and is taken to a role-specific workspace. Clinic staff coordinate visits; doctors review patients and record care; patients see only their own care information.', 'Bodyx')]
role_data=[[P('<b>Doctor</b><br/>Reviews assigned patients, appointments, dental findings, periodontal notes, prescriptions, treatment plans, and invoices.', 'Smallx'), P('<b>Patient</b><br/>Views their own dashboard, appointments, records, treatment plan, prescriptions, and bills.', 'Smallx')], [P('<b>Reception / Admin</b><br/>Manages registration, appointments, queue operations, branches, staff, inventory, reports, settings, and billing.', 'Smallx'), P('<b>MySQL</b><br/>Stores users, patients, doctors, appointments, queue tokens, clinical records, plans, invoices, payments, and audits.', 'Smallx')]]
t=Table(role_data, colWidths=[88*mm,88*mm]); t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.5,colors.HexColor('#CBD5E1')),('BACKGROUND',(0,0),(-1,-1),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),('PADDING',(0,0),(-1,-1),8)])); story += [t]
story += [P('2. System architecture', 'H2x'), flow([('Browser\nHTML + CSS + JS', BLUE), ('Flask routes\nPages + JSON APIs', TEAL), ('SQLAlchemy\nModels + relationships', BLUE), ('MySQL\nPersistent data', TEAL)]), Spacer(1,5*mm), P('The browser sends normal page requests and fetch requests. Flask authenticates the session, validates the request, calls SQLAlchemy, and returns HTML or JSON. PyMySQL connects SQLAlchemy to the existing MySQL database. Local cartoon avatars are served from /static/img. Passwords are stored as hashes.', 'Bodyx')]
story += [P('Request lifecycle', 'H3x')]
for n in ['User clicks a link or submits a form.', 'Flask matches the URL to a blueprint route.', 'Flask-Login checks the session and role.', 'The route reads or changes SQLAlchemy model objects.', 'SQLAlchemy reads or writes MySQL.', 'Flask returns HTML or JSON.', 'JavaScript renders success, empty, loading, or error states.']:
    story.append(P(n, 'Bodyx'))

story += [PageBreak(), P('3. Complete clinic workflow', 'H2x'), flow([('Reception\nCheck in', TEAL), ('Queue\nCall / start', BLUE), ('Doctor\nExamine', TEAL), ('Tooth chart\nRecord', BLUE)]), Spacer(1,8*mm), flow([('Treatment plan', BLUE), ('Invoice', TEAL), ('Payment', BLUE), ('Follow-up', TEAL)])]
story += [P('Doctor flow: Aravind example', 'H3x'), P('Doctor signs in -> Dashboard -> Patients -> Aravind -> Clinical profile -> Dental Chart -> tooth 16 -> clinical finding -> Treatment Plan -> Invoice -> Payment -> Follow-up.', 'Bodyx'), P('Patient flow', 'H3x'), P('Patient signs in -> Patient Dashboard -> next appointment -> My Records -> Dental History -> Treatment Plan -> Prescription -> Bill. Patient navigation does not expose staff, inventory, other patients, or clinic-wide analytics.', 'Bodyx')]
story += [P('4. Main route map', 'H2x')]
route_rows=[[P('<b>Area</b>','Smallx'),P('<b>Routes</b>','Smallx'),P('<b>Purpose</b>','Smallx')],[P('Landing','Smallx'),P('/','Smallx'),P('Public welcome or authenticated dashboard.','Smallx')],[P('Auth','Smallx'),P('/login, /logout, /register','Smallx'),P('Sign in, sign out, create doctor/patient account.','Smallx')],[P('Dashboard','Smallx'),P('/dashboard, /api/dashboard','Smallx'),P('Role dashboard and operational JSON.','Smallx')],[P('Patients','Smallx'),P('/patients, /patients/&lt;id&gt;','Smallx'),P('Directory and clinical profile.','Smallx')],[P('Clinical','Smallx'),P('/clinical, /api/patients/&lt;id&gt;/teeth','Smallx'),P('Dental chart, perio, prescriptions, voice notes.','Smallx')],[P('Operations','Smallx'),P('/appointments, /queue, /staff','Smallx'),P('Visits, queue, care team.','Smallx')],[P('Finance','Smallx'),P('/treatment-plans, /billing','Smallx'),P('Plans, invoices, receipts, payments.','Smallx')],[P('Health','Smallx'),P('/api/health, /favicon.ico','Smallx'),P('MySQL health and brand icon.','Smallx')]]
t=Table(route_rows,colWidths=[28*mm,58*mm,90*mm]);t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.4,colors.HexColor('#CBD5E1')),('BACKGROUND',(0,0),(-1,0),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),('PADDING',(0,0),(-1,-1),5)]));story += [t]

story += [PageBreak(), P('5. Data model map', 'H2x')]
model_rows=[[P('<b>Model</b>','Smallx'),P('<b>What it stores</b>','Smallx'),P('<b>Connected records</b>','Smallx')],[P('User','Smallx'),P('Email, password hash, role, branch, avatar, login identity.','Smallx'),P('Doctor profile, audit logs.','Smallx')],[P('Patient','Smallx'),P('Demographics, contact, balance, alert state.','Smallx'),P('Appointments, findings, prescriptions, plans, invoices, X-rays.','Smallx')],[P('Doctor','Smallx'),P('Specialty, experience, branch, avatar, rating.','Smallx'),P('Appointments, patients, shifts.','Smallx')],[P('Appointment / QueueToken','Smallx'),P('Visit date, status, procedure, emergency priority, queue state.','Smallx'),P('Patient, doctor, chair.','Smallx')],[P('Clinical records','Smallx'),P('ToothFinding, PeriodontalRecord, ClinicalNote, Prescription, XRayImage.','Smallx'),P('Patient and doctor.','Smallx')],[P('Finance','Smallx'),P('TreatmentPlan, phases, items, Invoice, Payment, EMIPlan.','Smallx'),P('Patient, doctor, appointment.','Smallx')]]
t=Table(model_rows,colWidths=[40*mm,75*mm,61*mm]);t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.4,colors.HexColor('#CBD5E1')),('BACKGROUND',(0,0),(-1,0),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),('PADDING',(0,0),(-1,-1),5)]));story += [t]
story += [P('6. Security and persistence rules', 'H2x')]
for x in ['Passwords are hashed with Werkzeug; plain passwords are not stored.', 'MySQL remains the configured database; normal startup does not drop tables.', 'Destructive demo reset requires explicit opt-in.', 'Patient HTML and API detail routes reject another patient record with HTTP 403.', 'API failures return friendly JSON messages instead of raw tracebacks.', 'Profile images are local cartoon SVG assets; clinical X-rays remain separate clinical records.']:
    story.append(P('- '+x, 'Bodyx'))
story += [P('7. Team responsibilities', 'H2x')]
team_rows=[[P('<b>Team</b>','Smallx'),P('<b>Owns</b>','Smallx'),P('<b>Done means</b>','Smallx')],[P('Frontend','Smallx'),P('Templates, CSS, JavaScript, responsive states.','Smallx'),P('Loading, success, empty, error, and mobile states work.','Smallx')],[P('Backend','Smallx'),P('Routes, auth, permissions, JSON contracts.','Smallx'),P('Status codes, validation, no unauthorized records.','Smallx')],[P('Data','Smallx'),P('Models, MySQL persistence, seed data.','Smallx'),P('Changes survive restart; reset is explicit.','Smallx')],[P('QA','Smallx'),P('Route, browser, API, responsive checks.','Smallx'),P('Login, dashboard, patient, chart, billing, health pass.','Smallx')],[P('Design','Smallx'),P('Visual language, cartoons, hierarchy, accessibility.','Smallx'),P('No broken images; readable desktop/mobile layouts.','Smallx')]]
t=Table(team_rows,colWidths=[30*mm,70*mm,76*mm]);t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.4,colors.HexColor('#CBD5E1')),('BACKGROUND',(0,0),(-1,0),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),('PADDING',(0,0),(-1,-1),5)]));story += [t]
story += [P('8. Run and test', 'H2x'), P('Install: pip install -r requirements.txt. Start: python app.py. Open: http://127.0.0.1:5000/. Health: http://127.0.0.1:5000/api/health should return status ok, database mysql, and database_connected true. Demo doctor: doctor@dentiflow.com / doctor123.', 'Bodyx'), P('Generated for the DentiFlow internship demonstration. Clinical records shown in the prototype are demo data only.', 'Smallx')]

doc=SimpleDocTemplate(str(PDF_PATH), pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=18*mm)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(PDF_PATH)
