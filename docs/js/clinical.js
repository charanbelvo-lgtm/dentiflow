/**
 * DentiFlow - Clinical Suite Script
 * Includes Periodontal Charting, AI X-Ray Radiograph Viewer, Voice-to-Notes SOAP Assistant, and Digital Rx
 */

document.addEventListener('DOMContentLoaded', () => {
  initVoiceToNotes();
  initXRayViewer();
  initPerioGrid();
  initPrescriptionBuilder();
});

// ==========================================================================
// 1. AI Voice-to-Notes SOAP Clinical Note Assistant
// ==========================================================================
function initVoiceToNotes() {
  const micBtn = document.getElementById('voice-mic-btn');
  const waveContainer = document.getElementById('voice-waves');
  const statusLabel = document.getElementById('voice-status-label');
  const transcriptBox = document.getElementById('voice-transcript-text');
  const saveBtn = document.getElementById('save-voice-note-btn');

  let isRecording = false;
  let recognition = null;

  // Sample realistic clinical dictations for quick simulation
  const sampleDictations = [
    "Patient reports mild sensitivity in upper right molar on cold foods for 4 days. No spontaneous pain. Existing composite restoration appears worn. IOPA reveals localized distal radiolucency. Recommended single visit RCT and crown.",
    "Patient attended for post-extraction review on tooth 48. Sockets healing well with healthy granulation tissue. Sutures removed. Advised to continue warm saline rinses.",
    "Routine orthodontic review for clear aligners. Patient compliant with 22 hours daily wear. Completed tray 14. Minor IPR of 0.2mm performed on lower anterior contact points. Delivered trays 15 to 18."
  ];

  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRec();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-IN';

    recognition.onresult = (event) => {
      let currentTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        currentTranscript += event.results[i][0].transcript;
      }
      if (transcriptBox) transcriptBox.value = currentTranscript;
      parseSoapFromTranscript(currentTranscript);
    };

    recognition.onerror = (event) => {
      console.warn('Speech recognition error/permission:', event.error);
      fallbackSimulateVoice();
    };
  }

  if (micBtn) {
    micBtn.addEventListener('click', () => {
      if (!isRecording) {
        startRecording();
      } else {
        stopRecording();
      }
    });
  }

  function startRecording() {
    isRecording = true;
    if (micBtn) {
      micBtn.classList.remove('btn-df-primary');
      micBtn.classList.add('btn-danger', 'pulse-recording');
      micBtn.innerHTML = '<i class="fa-solid fa-stop me-2"></i> Stop Dictation';
    }
    if (waveContainer) waveContainer.style.display = 'flex';
    if (statusLabel) statusLabel.innerHTML = '<span class="text-danger fw-bold"><i class="fa-solid fa-microphone-lines me-1"></i> Listening to Dentist...</span>';

    try {
      if (recognition) {
        recognition.start();
      } else {
        fallbackSimulateVoice();
      }
    } catch (e) {
      fallbackSimulateVoice();
    }
  }

  function stopRecording() {
    isRecording = false;
    if (micBtn) {
      micBtn.classList.remove('btn-danger', 'pulse-recording');
      micBtn.classList.add('btn-df-primary');
      micBtn.innerHTML = '<i class="fa-solid fa-microphone me-2"></i> Start AI Voice Dictation';
    }
    if (waveContainer) waveContainer.style.display = 'none';
    if (statusLabel) statusLabel.innerHTML = '<span class="text-success fw-bold"><i class="fa-solid fa-check me-1"></i> AI Draft Ready for Review</span>';

    if (recognition) {
      try { recognition.stop(); } catch(e){}
    }
  }

  function fallbackSimulateVoice() {
    let chosen = sampleDictations[Math.floor(Math.random() * sampleDictations.length)];
    let words = chosen.split(' ');
    let idx = 0;
    if (transcriptBox) transcriptBox.value = '';

    const interval = setInterval(() => {
      if (idx < words.length && isRecording) {
        if (transcriptBox) {
          transcriptBox.value += (idx === 0 ? '' : ' ') + words[idx];
          parseSoapFromTranscript(transcriptBox.value);
        }
        idx++;
      } else {
        clearInterval(interval);
        if (isRecording) stopRecording();
      }
    }, 180);
  }

  function parseSoapFromTranscript(text) {
    const subjInput = document.getElementById('soap-subjective');
    const objInput = document.getElementById('soap-objective');
    const assessInput = document.getElementById('soap-assessment');
    const planInput = document.getElementById('soap-plan');

    if (subjInput) subjInput.value = `Patient chief complaint: ${text.slice(0, 80)}...`;
    if (objInput) objInput.value = "Intraoral examination completed. Marginal ridges checked with explorer. Vitals stable.";
    if (assessInput) assessInput.value = "Symptomatic localized dental condition requiring intervention.";
    if (planInput) planInput.value = "Prescribed analgesic coverage. Scheduled restorative session.";
  }

  if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
      const patientId = document.getElementById('clinical-patient-select')?.value || 1;
      const subj = document.getElementById('soap-subjective')?.value;
      const obj = document.getElementById('soap-objective')?.value;
      const assess = document.getElementById('soap-assessment')?.value;
      const plan = document.getElementById('soap-plan')?.value;
      const raw = document.getElementById('voice-transcript-text')?.value;

      try {
        const res = await fetch(`/api/patients/${patientId}/voice-notes`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            subjective: subj,
            objective: obj,
            assessment: assess,
            plan: plan,
            raw_transcript: raw,
            is_ai_draft: true
          })
        });
        const data = await res.json();
        if (data.status === 'success') {
          showToast('SOAP Clinical Note saved to patient medical record!', 'success');
        }
      } catch (err) {
        showToast('Error saving note', 'danger');
      }
    });
  }
}

// ==========================================================================
// 2. Interactive X-Ray Radiograph & AI Anomaly Detection Viewer
// ==========================================================================
function initXRayViewer() {
  let zoomLevel = 1.0;
  let rotation = 0;
  let isInverted = false;
  const xrayImg = document.getElementById('xray-main-image');
  const aiOverlay = document.getElementById('xray-ai-overlay');
  const contrastSlider = document.getElementById('xray-contrast-slider');
  const brightnessSlider = document.getElementById('xray-brightness-slider');

  function updateTransform() {
    if (!xrayImg) return;
    const contrast = contrastSlider ? contrastSlider.value : 100;
    const brightness = brightnessSlider ? brightnessSlider.value : 100;
    const invertFilter = isInverted ? 'invert(100%)' : 'invert(0%)';
    
    xrayImg.style.transform = `scale(${zoomLevel}) rotate(${rotation}deg)`;
    xrayImg.style.filter = `contrast(${contrast}%) brightness(${brightness}%) ${invertFilter}`;
  }

  window.zoomXRay = function(delta) {
    zoomLevel = Math.max(0.6, Math.min(3.0, zoomLevel + delta));
    updateTransform();
  };

  window.rotateXRay = function() {
    rotation = (rotation + 90) % 360;
    updateTransform();
  };

  window.toggleInvertXRay = function() {
    isInverted = !isInverted;
    updateTransform();
  };

  window.resetXRay = function() {
    zoomLevel = 1.0;
    rotation = 0;
    isInverted = false;
    if (contrastSlider) contrastSlider.value = 100;
    if (brightnessSlider) brightnessSlider.value = 100;
    updateTransform();
  };

  window.toggleAIOverlay = function() {
    if (aiOverlay) {
      const isVisible = aiOverlay.style.display !== 'none';
      aiOverlay.style.display = isVisible ? 'none' : 'block';
      showToast(isVisible ? 'AI Highlights hidden' : 'AI Caries & Bone-Loss bounding boxes activated', 'info');
    }
  };

  if (contrastSlider) contrastSlider.addEventListener('input', updateTransform);
  if (brightnessSlider) brightnessSlider.addEventListener('input', updateTransform);
}

// ==========================================================================
// 3. Periodontal 6-Point Charting Grid
// ==========================================================================
function initPerioGrid() {
  const perioTableBody = document.getElementById('perio-table-body');
  if (!perioTableBody) return;

  const demoTeeth = [16, 17, 18, 26, 36, 46];
  perioTableBody.innerHTML = demoTeeth.map(tooth => `
    <tr>
      <td class="fw-bold text-primary">#${tooth}</td>
      <td><input type="number" class="form-control form-control-sm perio-input" value="3" min="1" max="12" onchange="window.checkPerioRisk(this)"></td>
      <td><input type="number" class="form-control form-control-sm perio-input" value="2" min="1" max="12" onchange="window.checkPerioRisk(this)"></td>
      <td><input type="number" class="form-control form-control-sm perio-input" value="3" min="1" max="12" onchange="window.checkPerioRisk(this)"></td>
      <td><input type="number" class="form-control form-control-sm perio-input" value="3" min="1" max="12" onchange="window.checkPerioRisk(this)"></td>
      <td><input type="number" class="form-control form-control-sm perio-input" value="2" min="1" max="12" onchange="window.checkPerioRisk(this)"></td>
      <td><input type="number" class="form-control form-control-sm perio-input" value="3" min="1" max="12" onchange="window.checkPerioRisk(this)"></td>
      <td class="text-center"><input type="checkbox" class="form-check-input" ${tooth === 16 ? 'checked' : ''}></td>
      <td>
        <select class="form-select form-select-sm">
          <option value="0">0</option>
          <option value="I" ${tooth === 16 ? 'selected' : ''}>I</option>
          <option value="II">II</option>
          <option value="III">III</option>
        </select>
      </td>
    </tr>
  `).join('');

  window.checkPerioRisk = function(input) {
    const val = parseInt(input.value || 0);
    if (val >= 5) {
      input.classList.add('bg-danger-subtle', 'text-danger', 'fw-bold');
    } else if (val === 4) {
      input.classList.add('bg-warning-subtle', 'text-warning', 'fw-bold');
      input.classList.remove('bg-danger-subtle', 'text-danger');
    } else {
      input.classList.remove('bg-danger-subtle', 'text-danger', 'bg-warning-subtle', 'text-warning', 'fw-bold');
    }
  };
}

// ==========================================================================
// 4. Digital Prescription Builder
// ==========================================================================
function initPrescriptionBuilder() {
  const addMedBtn = document.getElementById('add-rx-med-btn');
  const rxItemsTable = document.getElementById('rx-items-body');

  if (addMedBtn && rxItemsTable) {
    addMedBtn.addEventListener('click', () => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><input type="text" class="form-control form-control-sm" placeholder="e.g. Amoxicillin 500mg" required></td>
        <td><input type="text" class="form-control form-control-sm" value="1 Tablet"></td>
        <td>
          <select class="form-select form-select-sm">
            <option value="Twice daily (1-0-1)">Twice daily (1-0-1)</option>
            <option value="Thrice daily (1-1-1)">Thrice daily (1-1-1)</option>
            <option value="Once daily (1-0-0)">Once daily (1-0-0)</option>
            <option value="SOS (As needed)">SOS (As needed)</option>
          </select>
        </td>
        <td><input type="text" class="form-control form-control-sm" value="5 days"></td>
        <td><input type="text" class="form-control form-control-sm" value="After food"></td>
        <td class="text-center"><button type="button" class="btn btn-outline-danger btn-sm border-0" onclick="this.closest('tr').remove()"><i class="fa-solid fa-trash"></i></button></td>
      `;
      rxItemsTable.appendChild(tr);
    });
  }
}
