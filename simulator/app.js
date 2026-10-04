// ROAVAI Parent App & Wini Robot Simulator Engine

const API_BASE = 'http://localhost:4000/api';
const WS_URL = 'ws://localhost:4000';

let state = {
  currentChildId: 'child_leo',
  unlockedPin: false,
  enteredPin: '',
  selectedRevealTries: 2,
  probeMode: 'both',
  frustrationGuard: true,
  reasoningVisibility: true,
  pausedNow: false,
  privacy: {
    storeReasoning: true,
    voiceData: true,
    aiModel: false
  },
  // Tutor Robot Session State
  tutor: {
    questionIndex: 0,
    triesCount: 0,
    currentOptionChosen: null,
    isProbing: false,
    childStatedReason: '',
    frustrationDetected: false
  }
};

let wsSocket = null;

// Initialize Web App
document.addEventListener('DOMContentLoaded', async () => {
  initViewSwitchers();
  initThemeToggle();
  setupWebSocket();
  await loadChildData(state.currentChildId);
  renderMisconceptions();
});

// View Switchers
function initViewSwitchers() {
  const container = document.getElementById('main-container');
  const btnSplit = document.getElementById('btn-split-view');
  const btnPhone = document.getElementById('btn-phone-only');
  const btnRobot = document.getElementById('btn-robot-only');

  btnSplit.addEventListener('click', () => {
    container.className = 'main-container';
    setActiveViewBtn(btnSplit);
  });

  btnPhone.addEventListener('click', () => {
    container.className = 'main-container phone-only';
    setActiveViewBtn(btnPhone);
  });

  btnRobot.addEventListener('click', () => {
    container.className = 'main-container robot-only';
    setActiveViewBtn(btnRobot);
  });
}

function setActiveViewBtn(activeBtn) {
  document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
  activeBtn.classList.add('active');
}

// Theme Toggle
function initThemeToggle() {
  const toggleBtn = document.getElementById('theme-toggle');
  toggleBtn.addEventListener('click', () => {
    document.body.classList.toggle('light-mode');
    document.body.classList.toggle('dark-mode');
    toggleBtn.textContent = document.body.classList.contains('light-mode') ? '☀️' : '🌙';
  });
}

// PIN Security Lock Functions
function pressPin(num) {
  if (state.enteredPin.length < 4) {
    state.enteredPin += num;
    updatePinDots();
  }
  if (state.enteredPin.length === 4) {
    verifyPin();
  }
}

function clearPin() {
  state.enteredPin = state.enteredPin.slice(0, -1);
  updatePinDots();
}

function updatePinDots() {
  const dots = document.querySelectorAll('.pin-dot');
  dots.forEach((dot, idx) => {
    if (idx < state.enteredPin.length) {
      dot.classList.add('filled');
    } else {
      dot.classList.remove('filled');
    }
  });
}

function verifyPin() {
  if (state.enteredPin === '1234') {
    unlockApp();
  } else {
    alert('Incorrect PIN. Try 1234 or click Demo Auto-Unlock.');
    state.enteredPin = '';
    updatePinDots();
  }
}

function quickPassPin() {
  state.enteredPin = '1234';
  updatePinDots();
  setTimeout(unlockApp, 200);
}

function biometricUnlock() {
  unlockApp();
}

function unlockApp() {
  state.unlockedPin = true;
  document.getElementById('pin-lock-overlay').classList.add('unlocked');
}

// Tab Navigation
function switchTab(tabId, tabBtn) {
  document.querySelectorAll('.tab-item').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  
  tabBtn.classList.add('active');
  document.getElementById(tabId).classList.add('active');
}

// WebSocket Connection to Mock Backend (<30s Rule Sync PRD FR-4)
function setupWebSocket() {
  try {
    wsSocket = new WebSocket(WS_URL);
    
    wsSocket.onopen = () => {
      document.getElementById('sync-pill').innerHTML = `<span class="dot pulse"></span> WebSocket Online (&lt;30s Sync)`;
    };

    wsSocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('[WebSocket Received]', data);

      if (data.type === 'CONTROLS_UPDATED' || data.type === 'SYNC_INIT') {
        applyControlsToRobot(data.controls);
      }
    };

    wsSocket.onerror = (err) => {
      console.warn('[WebSocket Error] Falling back to REST polling', err);
      document.getElementById('sync-pill').innerHTML = `<span class="dot"></span> REST Sync Ready`;
    };
  } catch (e) {
    console.warn('WebSocket init failed, using REST');
  }
}

// Load Child Data & Controls from Backend
async function loadChildData(childId) {
  try {
    const resModel = await fetch(`${API_BASE}/learner-model/${childId}`);
    if (resModel.ok) {
      const model = await resModel.json();
      state.learnerModel = model;
      renderMisconceptions();
    }

    const resControls = await fetch(`${API_BASE}/controls/${childId}`);
    if (resControls.ok) {
      const controls = await resControls.json();
      state.selectedRevealTries = controls.answerRevealTries || 2;
      state.probeMode = controls.probeInputMode || 'both';
      state.frustrationGuard = controls.frustrationGuard !== false;
      state.reasoningVisibility = controls.reasoningVisibility !== false;
      state.pausedNow = !!controls.pausedNow;

      syncControlsUi();
      applyControlsToRobot(controls);
    }
  } catch (err) {
    console.warn('Backend API offline, using local fallback state', err);
  }
}

function switchChildProfile(childId) {
  state.currentChildId = childId;
  const avatar = childId === 'child_leo' ? '🚀' : '🎨';
  document.getElementById('current-child-avatar').textContent = avatar;
  loadChildData(childId);
}

// Render Misconception Diagnostics (PRD Section 4.3 & FR-6, FR-7)
function renderMisconceptions() {
  const container = document.getElementById('misconception-feed');
  const misconceptions = (state.learnerModel && state.learnerModel.misconceptions) || [
    {
      id: "misc_101",
      subject: "Physics",
      concept: "Gravity & Floating in Water",
      date: "Today, 4:15 PM",
      questionAsked: "Why do heavy ships float while small rocks sink?",
      childChoice: "Option B: Ships have air inside, so gravity turns off for them.",
      childStatedReason: "I picked B because when I go underwater in the pool I feel weightless so gravity stops working underwater.",
      parentTip: "Explain buoyancy as water pushing up against gravity, rather than gravity turning off underwater."
    }
  ];

  if (!state.reasoningVisibility) {
    container.innerHTML = `
      <div class="card">
        <p style="color: var(--text-muted); font-size: 12px; text-align: center;">
          🔒 Stated reasoning visibility is currently turned off in Tutoring Controls.
        </p>
      </div>`;
    return;
  }

  container.innerHTML = misconceptions.map(m => `
    <div class="card misc-card">
      <div class="misc-top">
        <span class="badge badge-warning">${m.subject}</span>
        <span class="misc-date">${m.date}</span>
      </div>
      <div class="misc-concept">${m.concept}</div>
      <div class="misc-q"><strong>Question:</strong> ${m.questionAsked}</div>
      <div class="misc-q"><strong>Child Picked:</strong> ${m.childChoice}</div>
      
      <div class="misc-reason-box">
        <div class="misc-reason-title">🗣️ Child's Stated Reason (from Wini Probe):</div>
        <div class="misc-reason-text">"${m.childStatedReason}"</div>
      </div>

      <div class="parent-tip-box">
        💡 <strong>Parent Tip:</strong> ${m.parentTip}
      </div>
    </div>
  `).join('');
}

// Control UI Actions & Controls Sync (PRD FR-4, FR-5)
function setRevealTries(tries, btn) {
  state.selectedRevealTries = tries;
  document.querySelectorAll('.segmented-control .segment-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('val-reveal-tries').textContent = `${tries} Tries`;
  saveControlsToBackend();
}

function updateControlState() {
  const slider = document.getElementById('time-limit-slider');
  document.getElementById('val-time-limit').textContent = `${slider.value} Mins`;

  state.probeMode = document.getElementById('probe-mode-select').value;
  state.frustrationGuard = document.getElementById('frustration-guard-toggle').checked;
  state.reasoningVisibility = document.getElementById('reasoning-visibility-toggle').checked;

  renderMisconceptions();
}

async function saveControlsToBackend() {
  const startTime = performance.now();
  const payload = {
    dailyTimeLimitMins: Number(document.getElementById('time-limit-slider').value),
    answerRevealTries: state.selectedRevealTries,
    probeInputMode: state.probeMode,
    frustrationGuard: state.frustrationGuard,
    reasoningVisibility: state.reasoningVisibility,
    pausedNow: state.pausedNow
  };

  try {
    const res = await fetch(`${API_BASE}/controls/${state.currentChildId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const latency = ((performance.now() - startTime) / 1000).toFixed(2);
    
    if (res.ok) {
      showSyncBanner(`Applied on Wini in ${latency}s (<30s sync rule met)`);
    }
  } catch (err) {
    showSyncBanner(`Local sync updated in 0.1s`);
  }

  applyControlsToRobot(payload);
}

function showSyncBanner(msg) {
  const banner = document.getElementById('sync-banner-text');
  banner.textContent = msg;
}

function togglePauseWini() {
  state.pausedNow = !state.pausedNow;
  const btn = document.getElementById('btn-pause-toggle');
  
  if (state.pausedNow) {
    btn.textContent = '▶️ Resume Wini';
    btn.style.background = 'var(--success-color)';
  } else {
    btn.textContent = '⏸️ Pause Wini';
    btn.style.background = 'var(--danger-color)';
  }

  saveControlsToBackend();
}

// Apply Controls live onto Wini Robot Simulator
function applyControlsToRobot(controls) {
  if (!controls) return;
  
  document.getElementById('ins-reveal-tries').textContent = `${controls.answerRevealTries || 2} Tries`;
  document.getElementById('ins-probe-mode').textContent = controls.probeInputMode || 'Voice or Tap';
  document.getElementById('ins-frustration').textContent = controls.frustrationGuard !== false ? 'ACTIVE (ON)' : 'OFF';

  const winiStatusBadge = document.getElementById('wini-live-status');
  const winiFace = document.getElementById('wini-face');
  const speech = document.getElementById('wini-speech-bubble');

  if (controls.pausedNow) {
    winiStatusBadge.textContent = 'PAUSED';
    winiStatusBadge.className = 'badge badge-warning';
    winiFace.className = 'wini-face paused';
    speech.textContent = '⏸️ Wini is currently paused by parent request.';
  } else {
    winiStatusBadge.textContent = 'Online';
    winiStatusBadge.className = 'badge badge-online';
    if (!state.tutor.isProbing) {
      winiFace.className = 'wini-face';
      speech.textContent = 'Ready to learn with Leo!';
    }
  }
}

// QR Pairing Simulation (PRD FR-2)
async function simulateQrPairing() {
  const qrInput = document.getElementById('pairing-qr-input').value;
  try {
    const res = await fetch(`${API_BASE}/pairing/qr`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ childId: state.currentChildId, qrCodeData: qrInput })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      alert(`✅ Success: ${data.message} Device ID: ${data.deviceId}`);
      document.getElementById('app-wini-status').textContent = 'Wini Paired • Online';
    } else {
      alert(`❌ Pairing Error: ${data.error}`);
    }
  } catch (err) {
    alert('✅ Demo Pairing completed successfully! (Wini Robot linked)');
  }
}

// Privacy & Export / Delete (PRD FR-9)
function updatePrivacyState() {
  state.privacy.storeReasoning = document.getElementById('privacy-reasoning-toggle').checked;
  state.privacy.voiceData = document.getElementById('privacy-voice-toggle').checked;
  state.privacy.aiModel = document.getElementById('privacy-ai-toggle').checked;
}

async function exportChildData() {
  try {
    const res = await fetch(`${API_BASE}/privacy/export/${state.currentChildId}`);
    const data = await res.json();
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ROAVAI_Child_Data_${state.currentChildId}.json`;
    a.click();
  } catch (e) {
    alert('Downloading sample child export payload...');
  }
}

async function confirmDeleteChildProfile() {
  if (confirm('⚠️ Are you sure you want to delete this child profile? This will immediately lock Wini and schedule full deletion of learner history & reasoning data within 30 days.')) {
    try {
      const res = await fetch(`${API_BASE}/privacy/delete/${state.currentChildId}`, { method: 'DELETE' });
      const data = await res.json();
      alert(`✅ ${data.message}`);
    } catch (e) {
      alert('✅ Profile deletion initiated. Learner data scheduled for removal in 30 days.');
    }
  }
}

// Add Child Modal (FR-1)
function openAddChildModal() {
  document.getElementById('add-child-modal').classList.remove('hidden');
}

function closeAddChildModal() {
  document.getElementById('add-child-modal').classList.add('hidden');
}

async function submitNewChild() {
  const name = document.getElementById('new-child-name').value;
  const age = document.getElementById('new-child-age').value;
  const curriculum = document.getElementById('new-child-curriculum').value;
  const consent = document.getElementById('new-child-consent').checked;

  if (!consent) {
    alert('FR-1 Error: Parental consent must be checked before creating a child profile.');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/children`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, age, curriculum })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      alert(`✅ Child profile for ${data.child.name} created!`);
      closeAddChildModal();
    } else {
      alert(`Error: ${data.error}`);
    }
  } catch (err) {
    alert(`✅ Child profile for ${name || 'New Learner'} created!`);
    closeAddChildModal();
  }
}

// WINI ROBOT TUTORING PROBE-FIRST LOOP SIMULATOR
function chooseMcq(option) {
  if (state.pausedNow) {
    alert('Wini is currently paused by parent!');
    return;
  }

  state.tutor.currentOptionChosen = option;
  state.tutor.triesCount += 1;

  document.getElementById('tries-tag').textContent = `Try ${state.tutor.triesCount} of ${state.selectedRevealTries}`;

  if (option === 'A') {
    // Correct Answer
    triggerCorrectAnswer();
  } else {
    // Wrong Answer -> Trigger Probe-First Tutoring Flow!
    triggerWiniProbe(option);
  }
}

function triggerWiniProbe(option) {
  state.tutor.isProbing = true;
  const winiFace = document.getElementById('wini-face');
  const speech = document.getElementById('wini-speech-bubble');
  const probeBox = document.getElementById('probe-box');

  winiFace.className = 'wini-face probing';
  speech.textContent = `"Hmm, you picked Option ${option}! Why did you choose that one, Leo?"`;
  
  probeBox.classList.remove('hidden');
}

function simulateVoiceInput() {
  const voiceInput = document.getElementById('child-voice-sim-text');
  voiceInput.value = "Because when I go underwater in the pool I feel weightless so gravity stops working underwater!";
  alert('🎙️ Voice audio simulated and transcribed into text by Wini.');
}

function submitChildReasoning() {
  const reasoning = document.getElementById('child-voice-sim-text').value;
  state.tutor.childStatedReason = reasoning;

  // Check Frustration Guard (PRD 4.5 & FR-8)
  if (state.frustrationGuard && state.tutor.triesCount >= state.selectedRevealTries) {
    // Frustration Guard triggers hint/explanation
    showHintBox();
  } else if (state.tutor.triesCount >= state.selectedRevealTries) {
    // Reached answer reveal try limit (FR-5)
    showRevealBox();
  } else {
    showHintBox();
  }

  // Push new misconception entry to parent app feed!
  const newMisc = {
    id: `misc_${Date.now()}`,
    subject: "Science & Physics",
    concept: "Gravity underwater misconception",
    date: "Just Now",
    questionAsked: "Why do heavy ships float while small pebbles sink?",
    childChoice: `Option ${state.tutor.currentOptionChosen}`,
    childStatedReason: reasoning,
    parentTip: "Buoyancy is water pushing up against gravity, rather than gravity shutting off."
  };

  if (!state.learnerModel) state.learnerModel = { misconceptions: [] };
  state.learnerModel.misconceptions.unshift(newMisc);
  renderMisconceptions();
}

function showHintBox() {
  document.getElementById('probe-box').classList.add('hidden');
  document.getElementById('hint-box').classList.remove('hidden');
  document.getElementById('wini-speech-bubble').textContent = '"Here is a hint to help you rethink this question!"';
}

function showRevealBox() {
  document.getElementById('probe-box').classList.add('hidden');
  document.getElementById('hint-box').classList.add('hidden');
  document.getElementById('reveal-box').classList.remove('hidden');
  document.getElementById('wini-speech-bubble').textContent = '"Answer revealed so you are never stuck! Great effort!"';
}

function triggerCorrectAnswer() {
  const winiFace = document.getElementById('wini-face');
  const speech = document.getElementById('wini-speech-bubble');
  
  winiFace.className = 'wini-face';
  speech.textContent = '"🎉 Spot on, Leo! Water pushes upward with buoyancy equal to the weight of displaced water!"';
  
  document.getElementById('probe-box').classList.add('hidden');
  document.getElementById('hint-box').classList.add('hidden');
  document.getElementById('reveal-box').classList.remove('hidden');
}

function retryQuestion() {
  document.getElementById('hint-box').classList.add('hidden');
  document.getElementById('probe-box').classList.add('hidden');
  document.getElementById('wini-face').className = 'wini-face';
  document.getElementById('wini-speech-bubble').textContent = '"Give it another shot!"';
}

function resetTutorQuestion() {
  state.tutor.triesCount = 0;
  state.tutor.isProbing = false;
  document.getElementById('tries-tag').textContent = `Try 1 of ${state.selectedRevealTries}`;
  document.getElementById('probe-box').classList.add('hidden');
  document.getElementById('hint-box').classList.add('hidden');
  document.getElementById('reveal-box').classList.add('hidden');
  document.getElementById('wini-face').className = 'wini-face';
  document.getElementById('wini-speech-bubble').textContent = '"Ready for the next challenge?"';
}
