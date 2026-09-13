/**
 * DentiFlow - Executive Dashboard Script
 * Interactive Charts, KPI Counter Animations, Live Chair Matrix, Today's Queue & Timeline
 */

let revenueChartInstance = null;
let patientFlowChartInstance = null;
let acceptanceChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
  loadDashboardData();
  document.getElementById('dashboard-retry')?.addEventListener('click', loadDashboardData);
  animateCareJourney();
  // Auto refresh live operational status every 30 seconds
  setInterval(loadDashboardData, 30000);
});

function animateCareJourney() {
  const steps = [...document.querySelectorAll('.care-step')];
  if (!steps.length) return;
  let activeStep = 0;
  setInterval(() => {
    steps.forEach((step, index) => step.classList.toggle('active', index === activeStep));
    activeStep = (activeStep + 1) % steps.length;
  }, 2600);
}

async function loadDashboardData() {
  const errorPanel = document.getElementById('dashboard-error');
  if (errorPanel) errorPanel.hidden = true;
  try {
    const res = await fetch('/api/dashboard');
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.status === 'error') throw new Error(data.message || `Dashboard request failed (${res.status})`);

    renderKPIs(data.kpis);
    renderTimeline(data.timeline);
    renderChairs(data.chairs);
    renderQueue(data.queue);
    renderAlerts(data.alerts);
    renderCharts(data.charts);
    renderFollowups(data.upcoming_followups);
  } catch (err) {
    console.error('Error fetching dashboard data:', err);
    if (errorPanel) errorPanel.hidden = false;
  }
}

// 1. KPI Counters with smooth animation
function renderKPIs(kpis) {
  if (!kpis) return;

  animateValue('kpi-appointments', 0, kpis.today_appointments, 600);
  animateValue('kpi-waiting', 0, kpis.waiting_patients, 600);
  
  const revEl = document.getElementById('kpi-revenue');
  if (revEl) revEl.innerText = `₹${kpis.today_revenue.toLocaleString('en-IN')}`;

  const acceptEl = document.getElementById('kpi-acceptance');
  if (acceptEl) acceptEl.innerText = `${kpis.acceptance_rate}%`;

  const noShowEl = document.getElementById('kpi-noshow');
  if (noShowEl) noShowEl.innerText = `${kpis.no_show_rate}%`;

  const chairEl = document.getElementById('kpi-chairs');
  if (chairEl) chairEl.innerText = kpis.available_chairs;
}

function animateValue(id, start, end, duration) {
  const obj = document.getElementById(id);
  if (!obj) return;
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    obj.innerHTML = Math.floor(progress * (end - start) + start);
    if (progress < 1) {
      window.requestAnimationFrame(step);
    }
  };
  window.requestAnimationFrame(step);
}

// 2. Appointment Timeline
function renderTimeline(timeline) {
  const container = document.getElementById('dashboard-timeline-list');
  if (!container) return;

  if (!timeline || timeline.length === 0) {
    container.innerHTML = `<div class="text-center py-4 text-muted">No appointments scheduled for today.</div>`;
    return;
  }

  container.innerHTML = timeline.map(apt => {
    let statusClass = 'confirmed';
    if (apt.status === 'In Treatment') statusClass = 'in-treatment';
    else if (apt.status === 'Waiting') statusClass = 'waiting';
    else if (apt.status === 'Completed') statusClass = 'completed';
    else if (apt.status === 'Delayed') statusClass = 'delayed';

    return `
      <div class="d-flex align-items-center justify-content-between p-3 mb-2 rounded-3 border bg-white card-hover-lift">
        <div class="d-flex align-items-center gap-3">
          <div class="text-center p-2 rounded-3 bg-light border" style="min-width: 75px;">
            <span class="fw-bold text-primary" style="font-size: 13px;">${apt.start_time}</span>
          </div>
          <div>
            <div class="d-flex align-items-center gap-2">
              <span class="fw-bold text-dark" style="font-size: 14px;">${apt.patient_name}</span>
              ${apt.is_emergency ? '<span class="badge bg-danger-subtle text-danger border border-danger-subtle" style="font-size: 10px;">Emergency</span>' : ''}
            </div>
            <div class="text-muted" style="font-size: 12.5px;">
              ${apt.procedure_name} • <span class="text-dark fw-medium">${apt.doctor_name}</span> • <span class="badge bg-light text-secondary border">${apt.chair_name || 'Chair 01'}</span>
            </div>
          </div>
        </div>
        <div class="d-flex align-items-center gap-3">
          <span class="status-badge ${statusClass}">${apt.status}</span>
          <button class="btn btn-sm btn-light border" onclick="window.location.href='/patients/${apt.patient_id}'" title="View Patient Profile">
            <i class="fa-solid fa-arrow-up-right-from-square"></i>
          </button>
        </div>
      </div>
    `;
  }).join('');
}

// 3. Live Chair & Doctor Status Board
function renderChairs(chairs) {
  const container = document.getElementById('dashboard-chairs-grid');
  if (!container) return;

  if (!chairs || chairs.length === 0) return;

  container.innerHTML = chairs.map(c => {
    let cardBorder = 'border-light';
    let badgeClass = 'available';
    let iconClass = 'fa-chair text-success';
    
    if (c.status === 'In Treatment') {
      cardBorder = 'border-primary border-2 shadow-sm';
      badgeClass = 'in-treatment';
      iconClass = 'fa-tooth text-primary';
    } else if (c.status === 'Patient Waiting') {
      cardBorder = 'border-warning';
      badgeClass = 'waiting';
      iconClass = 'fa-clock text-warning';
    } else if (c.status === 'Cleaning') {
      cardBorder = 'border-purple';
      badgeClass = 'cleaning';
      iconClass = 'fa-spray-can-sparkles text-purple';
    }

    return `
      <div class="col-md-6 col-lg-3 mb-3">
        <div class="df-card h-100 p-3 ${cardBorder}">
          <div class="d-flex align-items-center justify-content-between mb-2">
            <span class="fw-bold text-dark" style="font-size: 14px;">${c.chair_number}</span>
            <span class="status-badge ${badgeClass}">${c.status}</span>
          </div>
          <div class="d-flex align-items-center gap-2 mb-2">
            <i class="fa-solid ${iconClass}"></i>
            <span class="text-muted" style="font-size: 12px;">${c.name}</span>
          </div>
          <div class="p-2 rounded-2 bg-light border mt-2">
            ${c.status === 'In Treatment' ? `
              <div class="fw-semibold text-dark" style="font-size: 13px;">${c.current_patient}</div>
              <div class="text-muted" style="font-size: 11.5px;">${c.current_procedure}</div>
              <div class="d-flex align-items-center justify-content-between mt-1 text-primary" style="font-size: 11.5px;">
                <span>${c.current_doctor}</span>
                <span class="fw-bold"><i class="fa-solid fa-stopwatch me-1"></i>${c.elapsed_minutes} min</span>
              </div>
            ` : (c.status === 'Patient Waiting' ? `
              <div class="text-warning fw-semibold" style="font-size: 12.5px;">Patient ready in lounge</div>
              <div class="text-muted" style="font-size: 11.5px;">${c.current_patient || 'Next in queue'}</div>
            ` : (c.status === 'Cleaning' ? `
              <div class="text-purple fw-semibold" style="font-size: 12.5px;">Sanitization in progress</div>
              <div class="text-muted" style="font-size: 11.5px;">Ready in approx ~5 min</div>
            ` : `
              <div class="text-success fw-semibold" style="font-size: 12.5px;">Ready for next patient</div>
              <div class="text-muted" style="font-size: 11.5px;">Operatory sterilized & ready</div>
            `))}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// 4. Today's Live Queue
function renderQueue(queue) {
  const container = document.getElementById('dashboard-queue-list');
  if (!container) return;

  if (!queue || queue.length === 0) {
    container.innerHTML = `<div class="text-center py-4 text-muted">Queue is currently empty.</div>`;
    return;
  }

  container.innerHTML = queue.slice(0, 4).map(token => `
    <div class="d-flex align-items-center justify-content-between p-3 mb-2 rounded-3 border bg-white">
      <div class="d-flex align-items-center gap-3">
        <span class="badge ${token.status === 'Serving' ? 'bg-primary' : 'bg-secondary'} px-2 py-2" style="font-size: 12px;">
          ${token.token_number}
        </span>
        <div>
          <div class="d-flex align-items-center gap-2">
            <span class="fw-bold text-dark" style="font-size: 13.5px;">${token.patient_name}</span>
            ${token.is_emergency ? '<span class="badge bg-danger" style="font-size: 9px;">EMERGENCY</span>' : ''}
          </div>
          <div class="text-muted" style="font-size: 12px;">
            ${token.procedure_name} • ${token.doctor_name}
          </div>
        </div>
      </div>
      <div class="d-flex align-items-center gap-2">
        ${token.status === 'Waiting' ? `
          <button class="btn btn-sm btn-outline-primary" onclick="triggerTokenAction(${token.id}, 'call')">
            <i class="fa-solid fa-bullhorn me-1"></i> Call
          </button>
          <button class="btn btn-sm btn-df-primary" onclick="triggerTokenAction(${token.id}, 'start')">
            Start
          </button>
        ` : `
          <button class="btn btn-sm btn-success" onclick="triggerTokenAction(${token.id}, 'complete')">
            <i class="fa-solid fa-check me-1"></i> Complete
          </button>
        `}
      </div>
    </div>
  `).join('');
}

async function triggerTokenAction(tokenId, action) {
  try {
    const res = await fetch(`/api/queue/${tokenId}/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: action })
    });
    const data = await res.json();
    if (data.status === 'success') {
      if (action === 'call') playChime('bell');
      showToast(`Token action updated: ${action}`, 'success');
      loadDashboardData();
    }
  } catch (e) {
    showToast('Error processing token action', 'danger');
  }
}
window.triggerTokenAction = triggerTokenAction;

// 5. Alerts Box
function renderAlerts(alerts) {
  const container = document.getElementById('dashboard-alerts-container');
  if (!container) return;

  if (!alerts || alerts.length === 0) {
    container.innerHTML = `<div class="text-center py-3 text-muted">All systems and alerts normal.</div>`;
    return;
  }

  container.innerHTML = alerts.map(a => `
    <div class="d-flex align-items-start gap-3 p-3 mb-2 rounded-3 bg-light border border-${a.type === 'danger' ? 'danger-subtle' : 'warning-subtle'}">
      <div class="text-${a.type}" style="font-size: 18px; margin-top: 2px;">
        <i class="fa-solid ${a.icon}"></i>
      </div>
      <div>
        <div class="fw-bold text-dark" style="font-size: 13px;">${a.title}</div>
        <div class="text-muted" style="font-size: 12px;">${a.description}</div>
      </div>
    </div>
  `).join('');
}

// 6. Upcoming Follow-ups
function renderFollowups(followups) {
  const container = document.getElementById('dashboard-followups-list');
  if (!container) return;

  if (!followups || followups.length === 0) return;

  container.innerHTML = followups.map(f => `
    <div class="d-flex align-items-center justify-content-between p-2 mb-2 border-bottom">
      <div>
        <div class="fw-semibold text-dark" style="font-size: 13px;">${f.patient_name}</div>
        <div class="text-muted" style="font-size: 11.5px;">${f.procedure} • ${f.doctor_name}</div>
      </div>
      <div class="text-end">
        <div class="badge bg-light text-dark border" style="font-size: 11px;">${f.date}</div>
      </div>
    </div>
  `).join('');
}

// 7. Interactive Chart.js Graphs
function renderCharts(chartsData) {
  if (!chartsData || typeof Chart === 'undefined') return;

  // Chart A: Revenue Trend
  const revCtx = document.getElementById('revenueTrendChart')?.getContext('2d');
  if (revCtx) {
    if (revenueChartInstance) revenueChartInstance.destroy();
    revenueChartInstance = new Chart(revCtx, {
      type: 'bar',
      data: {
        labels: chartsData.revenue_trend.labels,
        datasets: [{
          label: 'Revenue (₹)',
          data: chartsData.revenue_trend.values,
          backgroundColor: '#2563EB',
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `Revenue: ₹${ctx.raw.toLocaleString('en-IN')}`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (val) => `₹${(val / 1000)}k`
            }
          }
        }
      }
    });
  }

  // Chart B: Patient Flow
  const flowCtx = document.getElementById('patientFlowChart')?.getContext('2d');
  if (flowCtx) {
    if (patientFlowChartInstance) patientFlowChartInstance.destroy();
    patientFlowChartInstance = new Chart(flowCtx, {
      type: 'line',
      data: {
        labels: chartsData.patient_flow.labels,
        datasets: [
          {
            label: 'Returning Patients',
            data: chartsData.patient_flow.returning_patients,
            borderColor: '#2563EB',
            backgroundColor: 'rgba(37, 99, 235, 0.1)',
            fill: true,
            tension: 0.3
          },
          {
            label: 'New Patients',
            data: chartsData.patient_flow.new_patients,
            borderColor: '#10B981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            fill: true,
            tension: 0.3
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 12 } }
        }
      }
    });
  }

  // Chart C: Treatment Acceptance Donut
  const acceptCtx = document.getElementById('treatmentAcceptanceChart')?.getContext('2d');
  if (acceptCtx) {
    if (acceptanceChartInstance) acceptanceChartInstance.destroy();
    acceptanceChartInstance = new Chart(acceptCtx, {
      type: 'doughnut',
      data: {
        labels: chartsData.treatment_acceptance.labels,
        datasets: [{
          data: chartsData.treatment_acceptance.data,
          backgroundColor: chartsData.treatment_acceptance.colors,
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 11 } } }
        },
        cutout: '70%'
      }
    });
  }
}
