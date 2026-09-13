/**
 * DentiFlow - Interactive 32-Tooth Human Dental Chart
 * FDI World Dental Federation Notation (11-48)
 * Upper & Lower Arch interactive SVG rendering with surface diagnosis & cost calculation
 */

class DentalChart {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    this.patientId = options.patientId || 1;
    this.readOnly = options.readOnly || false;
    this.onToothSelect = options.onToothSelect || null;
    this.toothFindings = {}; // Map of toothNumber -> Finding Object
    
    this.teethData = {
      upperRight: [18, 17, 16, 15, 14, 13, 12, 11],
      upperLeft:  [21, 22, 23, 24, 25, 26, 27, 28],
      lowerRight: [48, 47, 46, 45, 44, 43, 42, 41],
      lowerLeft:  [31, 32, 33, 34, 35, 36, 37, 38]
    };

    this.statusColors = {
      'Healthy': '#10B981',
      'Watch': '#F59E0B',
      'Cavity': '#F97316',
      'Filling': '#3B82F6',
      'Crown': '#8B5CF6',
      'Root Canal': '#06B6D4',
      'Missing': '#9CA3AF',
      'Extraction': '#EF4444',
      'Implant': '#14B8A6'
    };

    this.treatmentPricing = {
      'Healthy': 0,
      'Watch': 0,
      'Cavity': 2500,       // Composite filling
      'Filling': 2000,      // Replacement restoration
      'Crown': 8500,        // Zirconia crown
      'Root Canal': 7500,   // Rotary RCT
      'Missing': 0,
      'Extraction': 3500,   // Surgical extraction
      'Implant': 35000      // Titanium implant
    };

    this.selectedTooth = null;
    this.init();
  }

  async init() {
    if (!this.container) return;
    this.renderSkeleton();
    await this.fetchFindings();
    this.renderChart();
  }

  renderSkeleton() {
    this.container.innerHTML = `
      <div class="text-center py-5">
        <div class="spinner-border text-primary" role="status"></div>
        <div class="mt-2 text-muted" style="font-size: 13px;">Loading 3D Dental Chart...</div>
      </div>
    `;
  }

  async fetchFindings() {
    try {
      const res = await fetch(`/api/patients/${this.patientId}/teeth`);
      const data = await res.json();
      if (data.findings) {
        data.findings.forEach(f => {
          this.toothFindings[f.tooth_number] = f;
        });
      }
    } catch (e) {
      console.error('Failed to load tooth findings:', e);
    }
  }

  renderChart() {
    const html = `
      <div class="dental-chart-wrapper w-100">
        <!-- Arch Selector / Stats Header -->
        <div class="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom">
          <div>
            <span class="fw-bold text-dark" style="font-size: 15px;">Adult Dentition (32 Teeth)</span>
            <span class="text-muted ms-2" style="font-size: 12px;">Universal FDI Two-Digit Notation</span>
          </div>
          <div class="d-flex align-items-center gap-2">
            <span class="badge bg-primary-subtle text-primary border px-3 py-2" id="chart-total-estimate">
              <i class="fa-solid fa-calculator me-1"></i> Estimated Treatment: <strong>₹0</strong>
            </span>
          </div>
        </div>

        <!-- Upper Arch -->
        <div class="arch-section mb-4">
          <div class="text-center mb-2">
            <span class="badge bg-light text-secondary border text-uppercase" style="font-size: 11px; letter-spacing: 0.5px;">Maxillary Arch (Upper Jaw)</span>
          </div>
          <div class="d-flex justify-content-center gap-4 flex-wrap">
            <div class="d-flex gap-1 justify-content-end" style="flex: 1; max-width: 360px;">
              ${this.teethData.upperRight.map(t => this.generateToothSVG(t, 'upper')).join('')}
            </div>
            <div class="arch-divider" style="width: 2px; background: #E2E8F0; height: 75px;"></div>
            <div class="d-flex gap-1 justify-content-start" style="flex: 1; max-width: 360px;">
              ${this.teethData.upperLeft.map(t => this.generateToothSVG(t, 'upper')).join('')}
            </div>
          </div>
        </div>

        <!-- Lower Arch -->
        <div class="arch-section">
          <div class="d-flex justify-content-center gap-4 flex-wrap">
            <div class="d-flex gap-1 justify-content-end" style="flex: 1; max-width: 360px;">
              ${this.teethData.lowerRight.map(t => this.generateToothSVG(t, 'lower')).join('')}
            </div>
            <div class="arch-divider" style="width: 2px; background: #E2E8F0; height: 75px;"></div>
            <div class="d-flex gap-1 justify-content-start" style="flex: 1; max-width: 360px;">
              ${this.teethData.lowerLeft.map(t => this.generateToothSVG(t, 'lower')).join('')}
            </div>
          </div>
          <div class="text-center mt-2">
            <span class="badge bg-light text-secondary border text-uppercase" style="font-size: 11px; letter-spacing: 0.5px;">Mandibular Arch (Lower Jaw)</span>
          </div>
        </div>

        <!-- Interactive Legend -->
        <div class="tooth-legend-bar">
          ${Object.entries(this.statusColors).map(([status, color]) => `
            <div class="legend-chip">
              <span class="legend-color" style="background-color: ${color};"></span>
              <span>${status}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    this.container.innerHTML = html;
    this.bindEvents();
    this.updateTotalEstimate();
  }

  generateToothSVG(toothNumber, archType) {
    const finding = this.toothFindings[toothNumber] || { status: 'Healthy' };
    const status = finding.status || 'Healthy';
    const color = this.statusColors[status] || '#10B981';
    const isSelected = this.selectedTooth === toothNumber;

    // Anatomical Tooth SVG with distinct 5-surface geometry
    return `
      <div class="tooth-cell text-center" style="width: 40px;" data-tooth="${toothNumber}" onclick="window.currentDentalChart.selectTooth(${toothNumber})">
        <div class="tooth-number-label text-muted mb-1" style="font-size: 11px; font-weight: 600;">${toothNumber}</div>
        <div class="tooth-svg-box ${isSelected ? 'selected' : ''}" style="cursor: pointer; transition: transform 0.15s ease;">
          <svg width="38" height="48" viewBox="0 0 40 50" class="tooth-graphic">
            <!-- Tooth Crown Base -->
            <rect x="4" y="4" width="32" height="42" rx="8" fill="#FFFFFF" stroke="${color}" stroke-width="${isSelected ? '3' : '2'}" />
            
            <!-- 5 Anatomical Surfaces (Occlusal center, Buccal top, Lingual bottom, Mesial left, Distal right) -->
            <!-- Top surface (Buccal/Facial) -->
            <polygon points="4,4 36,4 28,12 12,12" fill="${status === 'Cavity' && (finding.surfaces||'').includes('B') ? '#F97316' : '#F1F5F9'}" stroke="#CBD5E1" stroke-width="0.8" />
            <!-- Bottom surface (Lingual) -->
            <polygon points="4,46 36,46 28,38 12,38" fill="${status === 'Cavity' && (finding.surfaces||'').includes('L') ? '#F97316' : '#F1F5F9'}" stroke="#CBD5E1" stroke-width="0.8" />
            <!-- Left surface (Mesial) -->
            <polygon points="4,4 12,12 12,38 4,46" fill="${status === 'Cavity' && (finding.surfaces||'').includes('M') ? '#F97316' : '#F1F5F9'}" stroke="#CBD5E1" stroke-width="0.8" />
            <!-- Right surface (Distal) -->
            <polygon points="36,4 28,12 28,38 36,46" fill="${status === 'Cavity' && (finding.surfaces||'').includes('D') ? '#F97316' : '#F1F5F9'}" stroke="#CBD5E1" stroke-width="0.8" />
            <!-- Center surface (Occlusal / Incisal) -->
            <rect x="12" y="12" width="16" height="26" rx="4" fill="${color}" fill-opacity="0.85" stroke="#94A3B8" stroke-width="0.8" />
            
            ${status === 'Root Canal' ? '<line x1="20" y1="8" x2="20" y2="42" stroke="#FFFFFF" stroke-width="2.5" stroke-dasharray="2,2"/>' : ''}
            ${status === 'Extraction' ? '<line x1="8" y1="8" x2="32" y2="42" stroke="#FFFFFF" stroke-width="2.5"/><line x1="32" y1="8" x2="8" y2="42" stroke="#FFFFFF" stroke-width="2.5"/>' : ''}
            ${status === 'Implant' ? '<circle cx="20" cy="25" r="5" fill="#FFFFFF"/><line x1="20" y1="12" x2="20" y2="38" stroke="#102A43" stroke-width="2"/>' : ''}
          </svg>
        </div>
        <div class="tooth-status-dot mt-1 mx-auto" style="width: 6px; height: 6px; border-radius: 50%; background-color: ${color};"></div>
      </div>
    `;
  }

  selectTooth(toothNumber) {
    this.selectedTooth = toothNumber;
    const finding = this.toothFindings[toothNumber] || {
      tooth_number: toothNumber,
      status: 'Healthy',
      surfaces: '',
      diagnosis: 'Healthy intact tooth structure',
      recommended_treatment: 'None',
      estimated_cost: 0
    };

    if (this.onToothSelect) {
      this.onToothSelect(finding);
    } else {
      this.openFindingModal(finding);
    }
  }

  openFindingModal(finding) {
    let modal = document.getElementById('tooth-finding-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'tooth-finding-modal';
      modal.className = 'modal fade';
      modal.tabIndex = -1;
      document.body.appendChild(modal);
    }

    const color = this.statusColors[finding.status] || '#10B981';

    modal.innerHTML = `
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content shadow-lg border-0">
          <div class="modal-header bg-light">
            <div class="d-flex align-items-center gap-2">
              <div class="kpi-icon-box kpi-icon-blue" style="width: 36px; height: 36px;">
                <i class="fa-solid fa-tooth"></i>
              </div>
              <div>
                <h5 class="modal-title mb-0" style="font-size: 16px;">Tooth Finding — #${finding.tooth_number}</h5>
                <span class="text-muted" style="font-size: 12px;">Maxillary / Mandibular Quadrant Record</span>
              </div>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body p-4">
            <form id="tooth-finding-form">
              <input type="hidden" name="tooth_number" value="${finding.tooth_number}">
              
              <div class="mb-3">
                <label class="form-label">Clinical Status / Condition</label>
                <select class="form-select" name="status" id="modal-tooth-status" onchange="window.currentDentalChart.onStatusChange(this.value)">
                  ${Object.keys(this.statusColors).map(s => `
                    <option value="${s}" ${finding.status === s ? 'selected' : ''}>${s}</option>
                  `).join('')}
                </select>
              </div>

              <div class="mb-3">
                <label class="form-label">Surfaces Involved</label>
                <div class="d-flex gap-2">
                  ${['M', 'O', 'D', 'B', 'L'].map(surf => `
                    <label class="btn btn-outline-secondary btn-sm flex-fill">
                      <input type="checkbox" name="surfaces" value="${surf}" ${(finding.surfaces||'').includes(surf) ? 'checked' : ''}> ${surf}
                    </label>
                  `).join('')}
                </div>
                <small class="text-muted">M: Mesial, O: Occlusal, D: Distal, B: Buccal, L: Lingual</small>
              </div>

              <div class="mb-3">
                <label class="form-label">Diagnosis</label>
                <input type="text" class="form-control" name="diagnosis" id="modal-tooth-diagnosis" value="${finding.diagnosis || ''}" placeholder="e.g. Deep dental caries with pulp exposure">
              </div>

              <div class="mb-3">
                <label class="form-label">Recommended Treatment</label>
                <input type="text" class="form-control" name="recommended_treatment" id="modal-tooth-treatment" value="${finding.recommended_treatment || ''}" placeholder="e.g. Rotary Root Canal + 3D Zirconia Crown">
              </div>

              <div class="mb-3">
                <label class="form-label">Estimated Treatment Fee (₹ INR)</label>
                <div class="input-group">
                  <span class="input-group-text">₹</span>
                  <input type="number" class="form-control" name="estimated_cost" id="modal-tooth-cost" value="${finding.estimated_cost || 0}">
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer bg-light">
            <button type="button" class="btn btn-df-secondary" data-bs-dismiss="modal">Cancel</button>
            <button type="button" class="btn btn-df-primary" onclick="window.currentDentalChart.saveFindingFromModal()">
              <i class="fa-solid fa-check me-1"></i> Save Clinical Finding
            </button>
          </div>
        </div>
      </div>
    `;

    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
  }

  onStatusChange(newStatus) {
    const costInput = document.getElementById('modal-tooth-cost');
    const diagInput = document.getElementById('modal-tooth-diagnosis');
    const treatInput = document.getElementById('modal-tooth-treatment');

    if (costInput) costInput.value = this.treatmentPricing[newStatus] || 0;
    
    if (newStatus === 'Cavity') {
      if (diagInput) diagInput.value = 'Dental caries on enamel/dentin';
      if (treatInput) treatInput.value = 'Composite Nano-Hybrid Restoration';
    } else if (newStatus === 'Root Canal') {
      if (diagInput) diagInput.value = 'Irreversible Pulpitis with Periapical Lucency';
      if (treatInput) treatInput.value = 'Single-Visit Rotary RCT + CAD/CAM Crown';
    } else if (newStatus === 'Crown') {
      if (diagInput) diagInput.value = 'Gross structural loss / Post-Endodontic tooth';
      if (treatInput) treatInput.value = 'Monolithic 3D Zirconia Crown';
    } else if (newStatus === 'Implant') {
      if (diagInput) diagInput.value = 'Edentulous space / Missing tooth';
      if (treatInput) treatInput.value = 'Titanium Dental Implant + Custom Abutment';
    } else if (newStatus === 'Extraction') {
      if (diagInput) diagInput.value = 'Impacted third molar / Non-restorable root';
      if (treatInput) treatInput.value = 'Surgical Disimpaction / Extraction';
    }
  }

  async saveFindingFromModal() {
    const form = document.getElementById('tooth-finding-form');
    if (!form) return;

    const formData = new FormData(form);
    const toothNum = parseInt(formData.get('tooth_number'));
    const status = formData.get('status');
    const diagnosis = formData.get('diagnosis');
    const treatment = formData.get('recommended_treatment');
    const cost = parseFloat(formData.get('estimated_cost') || 0);

    const checkedSurfaces = Array.from(form.querySelectorAll('input[name="surfaces"]:checked')).map(cb => cb.value).join('');

    const payload = {
      tooth_number: toothNum,
      status: status,
      surfaces: checkedSurfaces,
      diagnosis: diagnosis,
      recommended_treatment: treatment,
      estimated_cost: cost
    };

    try {
      const res = await fetch(`/api/patients/${this.patientId}/teeth`, {
        method: 'POST',
        headers: { 'Content-Content': 'application/json', 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.status === 'success') {
        this.toothFindings[toothNum] = data.finding;
        this.renderChart();
        showToast(`Tooth #${toothNum} condition saved: ${status}`, 'success');

        const modalEl = document.getElementById('tooth-finding-modal');
        const modalInstance = bootstrap.Modal.getInstance(modalEl);
        if (modalInstance) modalInstance.hide();
      }
    } catch (e) {
      console.error(e);
      showToast('Error saving tooth finding', 'danger');
    }
  }

  updateTotalEstimate() {
    const total = Object.values(this.toothFindings).reduce((sum, f) => sum + (f.estimated_cost || 0), 0);
    const badge = document.getElementById('chart-total-estimate');
    if (badge) {
      badge.innerHTML = `<i class="fa-solid fa-calculator me-1"></i> Estimated Treatment: <strong>₹${total.toLocaleString('en-IN')}</strong>`;
    }
  }

  bindEvents() {
    // Tooth click handling already inline via onclick
  }
}

window.DentalChart = DentalChart;
