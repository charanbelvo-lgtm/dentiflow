from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import (
    db, Invoice, Payment, Appointment, Patient, Doctor, TreatmentPlan, FeedbackNPS
)

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
def index():
    return render_template('reports.html')

@reports_bp.route('/api/reports')
@login_required
def get_reports_data():
    timeframe = request.args.get('timeframe', '30d') # today, 7d, 30d, 90d, 1y
    today = date.today()

    # Timeframe labels & multipliers
    if timeframe == 'today':
        labels = ['09:00', '11:00', '13:00', '15:00', '17:00', '19:00']
        revenue_vals = [8500, 14200, 9500, 18500, 12000, 6800]
        patient_counts = [2, 4, 3, 5, 3, 2]
    elif timeframe == '7d':
        labels = [(today - timedelta(days=i)).strftime('%a') for i in reversed(range(7))]
        revenue_vals = [42000, 38000, 52000, 49000, 64000, 58000, 48250]
        patient_counts = [28, 25, 34, 31, 42, 39, 32]
    elif timeframe == '90d':
        labels = ['May 2026', 'Jun 2026', 'Jul 2026', 'Aug 2026']
        revenue_vals = [1120000, 1245000, 1310000, 1420000]
        patient_counts = [740, 810, 860, 920]
    elif timeframe == '1y':
        labels = ['Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']
        revenue_vals = [980000, 1020000, 1150000, 1080000, 1200000, 1180000, 1290000, 1340000, 1380000, 1410000, 1450000, 1520000]
        patient_counts = [620, 650, 710, 680, 750, 730, 810, 840, 870, 890, 910, 960]
    else: # default 30d
        labels = [f'Week {i}' for i in range(1, 5)]
        revenue_vals = [295000, 340000, 318000, 382000]
        patient_counts = [185, 210, 195, 240]

    # Revenue by Procedure
    procedure_revenue = {
        'labels': ['Root Canal Therapy', 'Clear Aligners & Ortho', 'Zirconia Crowns & Bridges', 'Dental Implants', 'Cosmetic & Whitening', 'Preventive & Scaling'],
        'data': [32, 28, 16, 12, 8, 4],
        'colors': ['#2563EB', '#06B6D4', '#8B5CF6', '#14B8A6', '#F59E0B', '#10B981']
    }

    # Doctor Performance Revenue Share
    doctors = Doctor.query.all()
    doctor_share = {
        'labels': [d.name for d in doctors],
        'data': [465000, 395000, 280000, 310000],
        'colors': ['#2563EB', '#06B6D4', '#14B8A6', '#8B5CF6']
    }

    # Patient Satisfaction & NPS
    nps_distribution = {
        'promoters_pct': 82,
        'passives_pct': 14,
        'detractors_pct': 4,
        'net_score': '+78'
    }

    # Summary KPI Cards
    kpis = {
        'total_revenue': f"₹{sum(revenue_vals):,.0f}",
        'revenue_growth': "+14.8%",
        'total_patients': sum(patient_counts),
        'patient_growth': "+9.2%",
        'avg_revenue_per_patient': f"₹{round(sum(revenue_vals) / max(1, sum(patient_counts))):,.0f}",
        'treatment_acceptance_rate': "84.2%",
        'no_show_rate': "3.8%",
        'inventory_cost_ratio': "12.4%"
    }

    return jsonify({
        'kpis': kpis,
        'revenue_trend': {
            'labels': labels,
            'values': revenue_vals
        },
        'patient_growth': {
            'labels': labels,
            'values': patient_counts
        },
        'procedure_revenue': procedure_revenue,
        'doctor_share': doctor_share,
        'nps': nps_distribution
    })
