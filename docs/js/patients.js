/**
 * DentiFlow - Patient Management Directory Script
 * Real-time Search, Filters, Add Patient Modal, Export CSV
 */

document.addEventListener('DOMContentLoaded', () => {
  loadPatients();
  initPatientFilters();
  initAddPatientForm();
});

let allPatients = [];

async function loadPatients() {
  const search = document.getElementById('patient-search-input')?.value || '';
  const doctorId = document.getElementById('filter-doctor')?.value || '';
  const bloodGroup = document.getElementById('filter-blood')?.value || '';

  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (doctorId) params.append('doctor_id', doctorId);
  if (bloodGroup) params.append('blood_group', bloodGroup);

  try {
    const res = await fetch(`/api/patients?${params.toString()}`);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.message || `Patient request failed (${res.status})`);
    allPatients = data.patients || [];
    renderPatientTable(allPatients);
  } catch (e) {
    console.error('Error loading patients:', e);
    const tbody = document.getElementById('patients-table-body');
    if (tbody) tbody.innerHTML = '<tr><td colspan="8" class="text-center p-5 text-danger">Unable to load patients. Please refresh and try again.</td></tr>';
  }
}

function renderPatientTable(patients) {
  const tbody = document.getElementById('patients-table-body');
  const countBadge = document.getElementById('patients-total-count');
  if (countBadge) countBadge.innerText = `${patients.length} Patients`;

  if (!tbody) return;

  if (patients.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center py-5 text-muted">
          <i class="fa-solid fa-user-slash mb-2" style="font-size: 32px; opacity: 0.4;"></i>
          <h6>No patient records found</h6>
          <p class="small mb-0">Try changing your search terms or add a new patient.</p>
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = patients.map(p => `
    <tr class="align-middle">
      <td>
        <div class="d-flex align-items-center gap-3">
          <img src="${p.avatar || ''}" alt="${p.name}" class="rounded-circle border" style="width: 40px; height: 40px; object-fit: cover;" onerror="this.style.display='none'; this.nextElementSibling.querySelector('.avatar-fallback').style.display='flex';">
          <div>
            <span class="avatar-fallback rounded-circle border bg-primary text-white align-items-center justify-content-center" style="display:none;width:40px;height:40px;">${(p.name || '?')[0]}</span>
            <a href="/patients/${p.id}" class="fw-bold text-dark text-decoration-none hover-primary" style="font-size: 14px;">
              ${p.name}
            </a>
            <div class="text-muted" style="font-size: 12px;">
              <span class="badge bg-light text-secondary border font-monospace">${p.patient_id}</span>
              ${p.critical_alerts && p.critical_alerts.length > 0 ? '<span class="badge bg-danger-subtle text-danger border border-danger-subtle ms-1"><i class="fa-solid fa-triangle-exclamation"></i> Alert</span>' : ''}
            </div>
          </div>
        </div>
      </td>
      <td>
        <div style="font-size: 13px;">${p.age} yrs • ${p.gender}</div>
        <div class="text-muted" style="font-size: 11.5px;">Blood: <span class="badge bg-light text-dark border">${p.blood_group}</span></div>
      </td>
      <td>
        <div style="font-size: 13px;"><i class="fa-solid fa-phone me-1 text-muted"></i>${p.phone}</div>
        <div class="text-muted" style="font-size: 11.5px;">${p.email || 'No email registered'}</div>
      </td>
      <td>
        <div style="font-size: 13px;">${p.last_visit_formatted}</div>
      </td>
      <td>
        <div style="font-size: 13px;">${p.next_appointment_formatted}</div>
      </td>
      <td>
        <span class="fw-bold ${p.outstanding_balance > 0 ? 'text-danger' : 'text-success'}" style="font-size: 13.5px;">
          ₹${p.outstanding_balance.toLocaleString('en-IN')}
        </span>
      </td>
      <td>
        <div style="font-size: 13px;">${p.primary_doctor_name}</div>
        <div class="text-muted" style="font-size: 11.5px;">${p.branch_name}</div>
      </td>
      <td class="text-end">
        <a href="/patients/${p.id}" class="btn btn-sm btn-df-secondary me-1">
          <i class="fa-solid fa-folder-open me-1"></i> Profile
        </a>
        <a class="btn btn-sm btn-outline-primary" href="/book" title="Book appointment">
          <i class="fa-solid fa-calendar-plus"></i>
        </a>
      </td>
    </tr>
  `).join('');
}

function initPatientFilters() {
  const searchInput = document.getElementById('patient-search-input');
  const doctorSelect = document.getElementById('filter-doctor');
  const bloodSelect = document.getElementById('filter-blood');

  if (searchInput) {
    let timeout = null;
    searchInput.addEventListener('input', () => {
      clearTimeout(timeout);
      timeout = setTimeout(loadPatients, 250);
    });
  }

  if (doctorSelect) doctorSelect.addEventListener('change', loadPatients);
  if (bloodSelect) bloodSelect.addEventListener('change', loadPatients);
}

function initAddPatientForm() {
  const form = document.getElementById('add-patient-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    try {
      const res = await fetch('/api/patients', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast(`Patient ${data.patient.name} registered successfully!`, 'success');
        form.reset();
        const modalEl = document.getElementById('addPatientModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
        loadPatients();
      } else {
        showToast(data.message || 'Error creating patient', 'danger');
      }
    } catch (err) {
      showToast('Network error creating patient', 'danger');
    }
  });
}

// Export Patients to CSV
window.exportPatientsCSV = function() {
  if (allPatients.length === 0) {
    showToast('No patient data to export', 'warning');
    return;
  }

  const headers = ['Patient ID', 'Name', 'Age', 'Gender', 'Phone', 'Email', 'Blood Group', 'Primary Doctor', 'Outstanding (INR)', 'Total Spent (INR)'];
  const rows = allPatients.map(p => [
    p.patient_id,
    `"${p.name}"`,
    p.age,
    p.gender,
    p.phone,
    p.email || '',
    p.blood_group,
    `"${p.primary_doctor_name}"`,
    p.outstanding_balance,
    p.total_spent
  ]);

  const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', `DentiFlow_Patients_${new Date().toISOString().slice(0, 10)}.csv`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  showToast('Patient roster exported to CSV', 'success');
};
