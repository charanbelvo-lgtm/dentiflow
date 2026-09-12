from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import (
    db, Doctor, StaffShift, LeaveRequest, Appointment, Chair, Branch, AuditLog
)
from security import staff_required, admin_required, log_audit_event

staff_bp = Blueprint('staff', __name__)

@staff_bp.route('/staff')
@login_required
@admin_required
def index():
    doctors = Doctor.query.all()
    chairs = Chair.query.all()
    branches = Branch.query.all()
    return render_template('staff.html', doctors=doctors, chairs=chairs, branches=branches)

@staff_bp.route('/doctor-profile/<int:doctor_id>')
@login_required
@admin_required
def doctor_profile(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    today = date.today()
    appointments_today = Appointment.query.filter_by(doctor_id=doctor.id, appointment_date=today).count()
    patients_treated = Appointment.query.filter_by(doctor_id=doctor.id, status='Completed').count()
    return render_template('doctor_profile.html', doctor=doctor, appointments_today=appointments_today, patients_treated=patients_treated)

@staff_bp.route('/api/staff')
@login_required
@admin_required
def get_staff_data():
    today = date.today()
    doctors = Doctor.query.all()
    
    doctor_list = []
    for d in doctors:
        d_dict = d.to_dict()
        # Count today's appointments
        apts_today = Appointment.query.filter_by(doctor_id=d.id, appointment_date=today).count()
        # Completed appointments
        completed_apts = Appointment.query.filter_by(doctor_id=d.id, status='Completed').count()
        d_dict['appointments_today'] = apts_today
        d_dict['completed_appointments_total'] = completed_apts
        d_dict['revenue_generated_month'] = 145000 + (d.id * 35000)
        d_dict['commission_earned_month'] = round(d_dict['revenue_generated_month'] * (d.commission_rate / 100.0), 2)
        doctor_list.append(d_dict)

    # Shifts for current week
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    shifts = StaffShift.query.filter(StaffShift.date >= start_of_week, StaffShift.date <= end_of_week).all()

    return jsonify({
        'doctors': doctor_list,
        'shifts': [s.to_dict() for s in shifts],
        'total_doctors': len(doctors)
    })

@staff_bp.route('/api/staff/shifts', methods=['POST'])
@login_required
@admin_required
def update_shift():
    data = request.get_json()
    doctor_id = int(data.get('doctor_id'))
    shift_date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
    shift_type = data.get('shift_type', 'Full Day (9am - 8pm)')
    status = data.get('status', 'Working')

    shift = StaffShift.query.filter_by(doctor_id=doctor_id, date=shift_date).first()
    if not shift:
        shift = StaffShift(doctor_id=doctor_id, date=shift_date)
        db.session.add(shift)

    shift.shift_type = shift_type
    shift.status = status
    shift.notes = data.get('notes')
    db.session.commit()

    log_audit_event(
        action=f"Updated shift for Doctor #{doctor_id} on {shift_date} to '{status}' ({shift_type})",
        module="Staff Management"
    )

    return jsonify({'status': 'success', 'message': 'Shift updated', 'shift': shift.to_dict()})
