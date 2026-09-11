/**
 * DentiFlow - Appointments & Scheduling Suite Script
 * Day / Week / Month Calendar, Interactive Filters, Status Transitions (Check-in, Start, Complete, Cancel)
 */

let currentViewDate = new Date();
let currentViewMode = 'day'; // day, week, month

document.addEventListener('DOMContentLoaded', () => {
  initDatePicker();
  loadAppointments();
  initNewAppointmentForm();
});

function initDatePicker() {
  const dateInput = document.getElementById('appointment-date-picker');
  if (dateInput) {
    dateInput.value = currentViewDate.toISOString().slice(0, 10);
    dateInput.addEventListener('change', (e) => {
      currentViewDate = new Date(e.target.value);
      loadAppointments();
    });
  }

  // Doctor & Chair filters
  const doctorFilter = document.getElementById('filter-apt-doctor');
  const chairFilter = document.getElementById('filter-apt-chair');
  const statusFilter = document.getElementById('filter-apt-status');

  if (doctorFilter) doctorFilter.addEventListener('change', loadAppointments);
  if (chairFilter) chairFilter.addEventListener('change', loadAppointments);
  if (statusFilter) statusFilter.addEventListener('change', loadAppointments);
}

window.changeAppointmentView = function(mode) {
  currentViewMode = mode;
  document.querySelectorAll('.btn-view-mode').forEach(btn => btn.classList.remove('active'));
  const activeBtn = document.getElementById(`btn-view-${mode}`);
  if (activeBtn) activeBtn.classList.add('active');
  loadAppointments();
};

window.navigateDate = function(offset) {
  if (currentViewMode === 'day') {
    currentViewDate.setDate(currentViewDate.getDate() + offset);
  } else if (currentViewMode === 'week') {
    currentViewDate.setDate(currentViewDate.getDate() + (offset * 7));
  } else if (currentViewMode === 'month') {
    currentViewDate.setMonth(currentViewDate.getMonth() + offset);
  }

  const dateInput = document.getElementById('appointment-date-picker');
  if (dateInput) dateInput.value = currentViewDate.toISOString().slice(0, 10);
  loadAppointments();
};

async function loadAppointments() {
  const dateStr = currentViewDate.toISOString().slice(0, 10);
  const doctorId = document.getElementById('filter-apt-doctor')?.value || '';
  const chairId = document.getElementById('filter-apt-chair')?.value || '';
  const status = document.getElementById('filter-apt-status')?.value || '';

  const params = new URLSearchParams({
    date: dateStr,
    view: currentViewMode
  });
  if (doctorId) params.append('doctor_id', doctorId);
  if (chairId) params.append('chair_id', chairId);
  if (status) params.append('status', status);

  try {
    const res = await fetch(`/api/appointments?${params.toString()}`);
    const data = await res.json();
    renderAppointments(data.appointments || []);
  } catch (err) {
    console.error('Error fetching appointments:', err);
  }
}

function renderAppointments(appointments) {
  const container = document.getElementById('appointments-grid-container');
  const countBadge = document.getElementById('appointments-count-badge');
  if (countBadge) countBadge.innerText = `${appointments.length} Scheduled`;

  if (!container) return;

  if (appointments.length === 0) {
    container.innerHTML = `
      <div class="text-center py-5 border rounded-3 bg-white w-100">
        <i class="fa-solid fa-calendar-xmark mb-2" style="font-size: 36px; opacity: 0.3;"></i>
        <h5>No appointments scheduled</h5>
        <p class="text-muted small">Your calendar is completely clear for this time slot.</p>
        <button class="btn btn-sm btn-df-primary" data-bs-toggle="modal" data-bs-target="#newAppointmentModal">
          <i class="fa-solid fa-plus me-1"></i> Book Appointment
        </button>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="row g-3">
      ${appointments.map(apt => `
        <div class="col-md-6 col-lg-4">
          <div class="df-card p-3 h-100 card-hover-lift ${apt.status === 'In Treatment' ? 'border-primary border-2 shadow-sm' : ''}">
            <div class="d-flex align-items-center justify-content-between mb-2">
              <span class="badge bg-light text-primary border fw-bold px-2 py-1">${apt.start_time} (${apt.duration_minutes}m)</span>
              <span class="status-badge ${apt.status.toLowerCase().replace(' ', '-')}">${apt.status}</span>
            </div>

            <div class="d-flex align-items-center gap-2 mb-2">
              <img src="${apt.patient_avatar || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&q=80&w=200'}" class="rounded-circle border" style="width: 38px; height: 38px; object-fit: cover;">
              <div style="flex: 1; overflow: hidden;">
                <div class="fw-bold text-dark text-truncate" style="font-size: 14px;">${apt.patient_name}</div>
                <div class="text-muted" style="font-size: 11.5px;">${apt.procedure_name}</div>
              </div>
            </div>

            <div class="p-2 rounded-2 bg-light border mb-3" style="font-size: 12px;">
              <div class="d-flex align-items-center justify-content-between">
                <span><i class="fa-solid fa-user-doctor text-muted me-1"></i> ${apt.doctor_name}</span>
                <span class="badge bg-white text-secondary border">${apt.chair_name || 'Chair 01'}</span>
              </div>
              <div class="text-muted mt-1">Source: <span class="badge bg-light text-dark">${apt.booking_source}</span></div>
            </div>

            <div class="d-flex align-items-center gap-1 border-top pt-2 mt-auto">
              ${apt.status === 'Confirmed' ? `
                <button class="btn btn-sm btn-outline-warning flex-fill" onclick="updateAptStatus(${apt.id}, 'Waiting')" title="Patient Arrived">
                  <i class="fa-solid fa-person-walking-arrow-right"></i> Check-in
                </button>
              ` : ''}
              ${apt.status === 'Waiting' ? `
                <button class="btn btn-sm btn-df-primary flex-fill" onclick="updateAptStatus(${apt.id}, 'In Treatment')">
                  <i class="fa-solid fa-tooth"></i> Start
                </button>
              ` : ''}
              ${apt.status === 'In Treatment' ? `
                <button class="btn btn-sm btn-success flex-fill" onclick="updateAptStatus(${apt.id}, 'Completed')">
                  <i class="fa-solid fa-check"></i> Complete
                </button>
              ` : ''}
              <button class="btn btn-sm btn-light border" onclick="window.location.href='/patients/${apt.patient_id}'" title="Patient Chart">
                <i class="fa-solid fa-folder-open"></i>
              </button>
              <button class="btn btn-sm btn-light border text-danger" onclick="updateAptStatus(${apt.id}, 'Cancelled')" title="Cancel Appointment">
                <i class="fa-solid fa-xmark"></i>
              </button>
            </div>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

async function updateAptStatus(aptId, newStatus) {
  try {
    const res = await fetch(`/api/appointments/${aptId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(`Appointment status updated to '${newStatus}'`, 'success');
      loadAppointments();
    }
  } catch (err) {
    showToast('Error updating status', 'danger');
  }
}
window.updateAptStatus = updateAptStatus;

function initNewAppointmentForm() {
  const form = document.getElementById('new-appointment-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    try {
      const res = await fetch('/api/appointments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast(`Appointment ${data.appointment.appointment_number} booked successfully!`, 'success');
        form.reset();
        const modalEl = document.getElementById('newAppointmentModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
        loadAppointments();
      }
    } catch (err) {
      showToast('Error booking appointment', 'danger');
    }
  });
}
