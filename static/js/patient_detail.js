/**
 * DentiFlow - Deep Patient Profile Suite Script
 * Comprehensive Clinical History, Tooth Chart, Treatment Plans, X-Rays, Invoices, Timeline
 */

let currentPatientId = null;

document.addEventListener('DOMContentLoaded', () => {
  const pathParts = window.location.pathname.split('/');
  currentPatientId = parseInt(pathParts[pathParts.length - 1]) || 1;

  loadPatientFullData(currentPatientId);
  initPatientActionModals();
});

async function loadPatientFullData(patientId) {
  try {
    const res = await fetch(`/api/patients/${patientId}`);
    const data = await res.json();

    renderPatientHeader(data.patient, data.alerts);
    renderClinicalTimeline(data.timeline);
    renderPatientAppointments(data.appointments);
    renderPatientTreatmentPlans(data.treatment_plans);
    renderPatientInvoices(data.invoices);
    renderPatientPrescriptions(data.prescriptions);
    renderPatientXRays(data.xrays);
    renderPatientFamily(data.family);
    renderPatientDocuments(data.documents);

    // Initialize Interactive Dental Tooth Chart in its container
    if (document.getElementById('patient-dental-chart-container')) {
      window.currentDentalChart = new DentalChart('patient-dental-chart-container', {
        patientId: patientId
      });
    }
  } catch (err) {
    console.error('Error fetching patient details:', err);
  }
}

// 1. Patient Header & Critical Medical Alert Banner
function renderPatientHeader(patient, alerts) {
  if (!patient) return;

  const nameEl = document.getElementById('patient-detail-name');
  if (nameEl) nameEl.innerText = patient.name;

  const idBadge = document.getElementById('patient-detail-id-badge');
  if (idBadge) idBadge.innerText = patient.patient_id;

  const infoSub = document.getElementById('patient-detail-info-sub');
  if (infoSub) infoSub.innerText = `${patient.age} yrs • ${patient.gender} • Blood Group: ${patient.blood_group} • Primary Doctor: ${patient.primary_doctor_name}`;

  const phoneEl = document.getElementById('patient-detail-phone');
  if (phoneEl) phoneEl.innerText = patient.phone;

  const emailEl = document.getElementById('patient-detail-email');
  if (emailEl) emailEl.innerText = patient.email || 'None';

  const healthIdEl = document.getElementById('patient-detail-health-id');
  if (healthIdEl) healthIdEl.innerText = patient.abdm_health_id || 'Not linked';

  const balanceEl = document.getElementById('patient-detail-balance');
  if (balanceEl) balanceEl.innerText = `₹${patient.outstanding_balance.toLocaleString('en-IN')}`;

  const spentEl = document.getElementById('patient-detail-spent');
  if (spentEl) spentEl.innerText = `₹${patient.total_spent.toLocaleString('en-IN')}`;

  // Medical Alert Banner
  const banner = document.getElementById('medical-alert-banner');
  if (banner) {
    if (alerts && alerts.length > 0) {
      banner.style.display = 'block';
      banner.innerHTML = `
        <div class="d-flex align-items-center gap-3">
          <div class="kpi-icon-box" style="background: rgba(239, 68, 68, 0.2); color: #EF4444; width: 38px; height: 38px;">
            <i class="fa-solid fa-triangle-exclamation" style="font-size: 18px;"></i>
          </div>
          <div style="flex: 1;">
            <div class="fw-bold text-danger" style="font-size: 13.5px;">CRITICAL MEDICAL / ALLERGY ALERT</div>
            <div class="text-dark" style="font-size: 13px;">
              ${alerts.map(a => `<span class="badge bg-danger-subtle text-danger border border-danger-subtle me-1 p-2">${a.alert_text}</span>`).join('')}
            </div>
          </div>
          <button class="btn btn-sm btn-outline-danger" onclick="openAddAlertModal()">+ Add Alert</button>
        </div>
      `;
    } else {
      banner.style.display = 'none';
    }
  }
}

// 2. Chronological Clinical Timeline
function renderClinicalTimeline(timeline) {
  const container = document.getElementById('patient-timeline-list');
  if (!container) return;

  if (!timeline || timeline.length === 0) {
    container.innerHTML = `<div class="text-center py-4 text-muted">No timeline events recorded yet.</div>`;
    return;
  }

  container.innerHTML = timeline.map(ev => `
    <div class="d-flex gap-3 mb-4 position-relative">
      <div class="timeline-icon-box rounded-circle d-flex align-items-center justify-content-center" style="width: 36px; height: 36px; background-color: ${ev.color}15; color: ${ev.color}; flex-shrink: 0; z-index: 1;">
        <i class="fa-solid ${ev.icon}" style="font-size: 15px;"></i>
      </div>
      <div class="df-card p-3 flex-fill border-light bg-white shadow-xs">
        <div class="d-flex align-items-center justify-content-between mb-1">
          <span class="fw-bold text-dark" style="font-size: 14px;">${ev.title}</span>
          <span class="text-muted" style="font-size: 12px;"><i class="fa-regular fa-clock me-1"></i>${ev.date}</span>
        </div>
        <div class="text-muted" style="font-size: 13px;">${ev.subtitle}</div>
      </div>
    </div>
  `).join('');
}

// 3. Appointments List
function renderPatientAppointments(appointments) {
  const container = document.getElementById('patient-appointments-list');
  if (!container) return;

  if (!appointments || appointments.length === 0) {
    container.innerHTML = `<div class="text-center py-4 text-muted">No appointments recorded.</div>`;
    return;
  }

  container.innerHTML = `
    <div class="df-table-container">
      <table class="df-table">
        <thead>
          <tr>
            <th>Appointment</th>
            <th>Date & Time</th>
            <th>Doctor</th>
            <th>Status</th>
            <th>Deposit</th>
          </tr>
        </thead>
        <tbody>
          ${appointments.map(a => `
            <tr>
              <td class="fw-bold text-primary">${a.appointment_number} <br><small class="text-muted fw-normal">${a.procedure_name}</small></td>
              <td>${a.appointment_date} <br><small class="text-muted">${a.start_time}</small></td>
              <td>${a.doctor_name}</td>
              <td><span class="status-badge ${a.status.toLowerCase().replace(' ', '-')}">${a.status}</span></td>
              <td>₹${a.deposit_amount}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}

// 4. Treatment Plans
function renderPatientTreatmentPlans(plans) {
  const container = document.getElementById('patient-treatment-plans-list');
  if (!container) return;

  if (!plans || plans.length === 0) {
    container.innerHTML = `
      <div class="text-center py-5 border rounded-3 bg-white">
        <i class="fa-solid fa-clipboard-list mb-2" style="font-size: 32px; opacity: 0.3;"></i>
        <h6>No active treatment plans</h6>
        <p class="small text-muted">Create a multi-phase treatment plan from the Treatment Planning module.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = plans.map(p => `
    <div class="df-card mb-3 p-4">
      <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-3">
        <div>
          <div class="d-flex align-items-center gap-2">
            <span class="fw-bold text-primary font-monospace">${p.plan_number}</span>
            <h5 class="mb-0 fw-bold">${p.title}</h5>
          </div>
          <small class="text-muted">Doctor: ${p.doctor_name} • Created: ${p.created_at}</small>
        </div>
        <div class="text-end">
          <span class="status-badge ${p.status.toLowerCase().replace(' ', '-')} me-2">${p.status}</span>
          <span class="fw-bold text-dark fs-5">₹${p.net_cost.toLocaleString('en-IN')}</span>
        </div>
      </div>

      <div class="phases-accordion mb-3">
        ${p.phases.map(phase => `
          <div class="p-3 mb-2 rounded-3 bg-light border">
            <div class="d-flex align-items-center justify-content-between mb-2">
              <span class="fw-bold text-dark" style="font-size: 13.5px;">${phase.title}</span>
              <span class="badge bg-secondary-subtle text-secondary border">Est. ₹${phase.phase_cost.toLocaleString('en-IN')}</span>
            </div>
            <div class="ps-2">
              ${phase.items.map(item => `
                <div class="d-flex align-items-center justify-content-between py-1 border-bottom border-white" style="font-size: 12.5px;">
                  <span>• Tooth #${item.tooth_number}: ${item.procedure_name}</span>
                  <span class="fw-medium">₹${item.net_cost.toLocaleString('en-IN')}</span>
                </div>
              `).join('')}
            </div>
          </div>
        `).join('')}
      </div>

      <div class="d-flex align-items-center justify-content-between pt-2 border-top">
        <div style="font-size: 13px;">
          <span>Accepted: <strong class="text-success">₹${p.accepted_amount.toLocaleString('en-IN')}</strong></span>
          <span class="ms-3">Pending: <strong class="text-warning">₹${p.pending_amount.toLocaleString('en-IN')}</strong></span>
        </div>
        <div class="d-flex gap-2">
          ${!p.is_converted_to_invoice ? `
            <button class="btn btn-sm btn-df-primary" onclick="convertPlanToInvoice(${p.id})">
              <i class="fa-solid fa-file-invoice-dollar me-1"></i> Convert to Invoice
            </button>
          ` : `
            <span class="badge bg-success-subtle text-success border p-2"><i class="fa-solid fa-check me-1"></i> Converted to Invoice</span>
          `}
        </div>
      </div>
    </div>
  `).join('');
}

async function convertPlanToInvoice(planId) {
  try {
    const res = await fetch(`/api/treatment-plans/${planId}/convert-to-invoice`, { method: 'POST' });
    const data = await res.json();
    if (data.status === 'success') {
      showToast('Treatment Plan converted to GST Invoice!', 'success');
      loadPatientFullData(currentPatientId);
    }
  } catch (e) {
    showToast('Error converting plan to invoice', 'danger');
  }
}
window.convertPlanToInvoice = convertPlanToInvoice;

// 5. Invoices & Payments
function renderPatientInvoices(invoices) {
  const container = document.getElementById('patient-invoices-list');
  if (!container) return;

  if (!invoices || invoices.length === 0) {
    container.innerHTML = `<div class="text-center py-4 text-muted">No invoices generated.</div>`;
    return;
  }

  container.innerHTML = `
    <div class="df-table-container">
      <table class="df-table">
        <thead>
          <tr>
            <th>Invoice</th>
            <th>Date</th>
            <th>Total Amount</th>
            <th>Paid</th>
            <th>Due</th>
            <th>Status</th>
            <th class="text-end">Actions</th>
          </tr>
        </thead>
        <tbody>
          ${invoices.map(inv => `
            <tr>
              <td class="fw-bold font-monospace text-primary">${inv.invoice_number}</td>
              <td>${inv.date_only}</td>
              <td class="fw-bold">₹${inv.total_amount.toLocaleString('en-IN')}</td>
              <td class="text-success fw-medium">₹${inv.paid_amount.toLocaleString('en-IN')}</td>
              <td class="${inv.due_amount > 0 ? 'text-danger fw-bold' : 'text-muted'}">₹${inv.due_amount.toLocaleString('en-IN')}</td>
              <td><span class="status-badge ${inv.status.toLowerCase()}">${inv.status}</span></td>
              <td class="text-end">
                <a href="/invoices/${inv.id}/print" target="_blank" class="btn btn-sm btn-light border">
                  <i class="fa-solid fa-print"></i>
                </a>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}

// 6. Prescriptions
function renderPatientPrescriptions(prescriptions) {
  const container = document.getElementById('patient-prescriptions-list');
  if (!container) return;

  if (!prescriptions || prescriptions.length === 0) {
    container.innerHTML = `<div class="text-center py-4 text-muted">No prescriptions issued.</div>`;
    return;
  }

  container.innerHTML = prescriptions.map(rx => `
    <div class="df-card mb-3 p-3">
      <div class="d-flex align-items-center justify-content-between mb-2 border-bottom pb-2">
        <div>
          <span class="fw-bold text-primary font-monospace">${rx.rx_number}</span>
          <span class="text-muted ms-2" style="font-size: 12.5px;">Issued: ${rx.date_formatted} by ${rx.doctor_name}</span>
        </div>
        <a href="/prescriptions/${rx.id}/print" target="_blank" class="btn btn-sm btn-outline-primary">
          <i class="fa-solid fa-print me-1"></i> Print Rx
        </a>
      </div>
      <div class="text-muted mb-2" style="font-size: 13px;">Diagnosis: <strong>${rx.diagnosis || 'General Prophylaxis'}</strong></div>
      <div class="table-responsive">
        <table class="table table-sm table-bordered mb-0" style="font-size: 12.5px;">
          <thead class="table-light">
            <tr>
              <th>Medicine</th>
              <th>Dosage</th>
              <th>Frequency</th>
              <th>Duration</th>
              <th>Instructions</th>
            </tr>
          </thead>
          <tbody>
            ${rx.items.map(it => `
              <tr>
                <td class="fw-semibold">${it.medicine_name}</td>
                <td>${it.dosage}</td>
                <td>${it.frequency}</td>
                <td>${it.duration}</td>
                <td>${it.instructions}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `).join('');
}

// 7. X-Rays / Imaging
function renderPatientXRays(xrays) {
  const container = document.getElementById('patient-xrays-list');
  if (!container) return;

  if (!xrays || xrays.length === 0) {
    container.innerHTML = `<div class="text-center py-4 text-muted">No dental radiographs found.</div>`;
    return;
  }

  container.innerHTML = `
    <div class="row">
      ${xrays.map(x => `
        <div class="col-md-6 mb-3">
          <div class="df-card p-3 h-100">
            <div class="d-flex align-items-center justify-content-between mb-2">
              <span class="fw-bold text-dark">${x.title}</span>
              <span class="badge bg-light text-dark border">${x.xray_type}</span>
            </div>
            <div class="xray-thumbnail-box rounded-3 overflow-hidden border mb-2 bg-dark text-center" style="height: 200px;">
              <img src="${x.image_url}" alt="${x.title}" style="width: 100%; height: 100%; object-fit: cover;">
            </div>
            <div class="p-2 rounded-2 bg-light border" style="font-size: 12px;">
              <div class="fw-bold text-primary"><i class="fa-solid fa-microchip me-1"></i> AI Indication (Confidence ${x.ai_confidence}%):</div>
              <div class="text-muted mt-1">${x.ai_analysis_notes}</div>
            </div>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

// 8. Family Accounts
function renderPatientFamily(family) {
  const container = document.getElementById('patient-family-list');
  if (!container) return;

  if (!family || family.length === 0) {
    container.innerHTML = `<div class="text-muted small py-2">No linked family members.</div>`;
    return;
  }

  container.innerHTML = family.map(f => `
    <div class="d-flex align-items-center justify-content-between p-2 mb-2 rounded-2 bg-light border">
      <div>
        <div class="fw-bold text-dark" style="font-size: 13px;">${f.name}</div>
        <small class="text-muted">${f.relation} • ${f.age ? f.age + ' yrs' : ''} • ${f.phone || ''}</small>
      </div>
      <span class="badge bg-primary-subtle text-primary border">Linked</span>
    </div>
  `).join('');
}

// 9. Documents
function renderPatientDocuments(documents) {
  const container = document.getElementById('patient-documents-list');
  if (!container) return;

  if (!documents || documents.length === 0) {
    container.innerHTML = `<div class="text-muted small py-2">No documents uploaded.</div>`;
    return;
  }

  container.innerHTML = documents.map(d => `
    <div class="d-flex align-items-center justify-content-between p-2 mb-2 rounded-2 bg-light border">
      <div class="d-flex align-items-center gap-2">
        <i class="fa-solid fa-file-pdf text-danger" style="font-size: 18px;"></i>
        <div>
          <div class="fw-bold text-dark" style="font-size: 13px;">${d.title}</div>
          <small class="text-muted">${d.doc_type} • ${d.file_size} • ${d.upload_date}</small>
        </div>
      </div>
      <a href="${d.file_url}" target="_blank" class="btn btn-sm btn-light border"><i class="fa-solid fa-download"></i></a>
    </div>
  `).join('');
}

function initPatientActionModals() {
  // Modal hooks
}

window.openAddAlertModal = function() {
  const alertText = prompt("Enter Critical Allergy / Medical Alert:", "ALLERGY: ");
  if (alertText && alertText.trim() !== "ALLERGY:") {
    fetch(`/api/patients/${currentPatientId}/alerts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ alert_text: alertText, is_critical: true })
    }).then(() => {
      showToast('Medical alert banner updated', 'warning');
      loadPatientFullData(currentPatientId);
    });
  }
};
