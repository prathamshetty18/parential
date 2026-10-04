const express = require('express');
const cors = require('cors');
const http = require('http');
const { WebSocketServer, WebSocket } = require('ws');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 4000;
const server = http.createServer(app);
const wss = new WebSocketServer({ server });

// Mock Database State
let state = {
  parent: {
    id: "parent_101",
    email: "sarah.jenkins@example.com",
    name: "Sarah Jenkins",
    pinCode: "1234",
    consentRecorded: true,
    consentTimestamp: "2026-10-01T09:15:00Z",
    consentMethod: "DPDP_VERIFIED_EMAIL"
  },
  children: [
    {
      id: "child_leo",
      name: "Leo",
      age: 8,
      grade: "3rd Grade",
      curriculum: "STEM Core & General Science",
      language: "English",
      avatar: "🚀",
      winiPaired: true,
      winiDeviceId: "WINI-ROBOT-8921",
      winiStatus: "online" // online | offline | paused
    },
    {
      id: "child_maya",
      name: "Maya",
      age: 11,
      grade: "6th Grade",
      curriculum: "Advanced Math & Physics Basics",
      language: "English",
      avatar: "🎨",
      winiPaired: false,
      winiDeviceId: null,
      winiStatus: "offline"
    }
  ],
  controls: {
    child_leo: {
      dailyTimeLimitMins: 45,
      timeSpentTodayMins: 28,
      bedtimeSchedule: { enabled: true, start: "20:00", end: "07:00" },
      pausedNow: false,
      subjectAllowlist: ["Math", "Science", "History"],
      contentLevel: "Ages 7-9",
      // Probe-First Tutoring Controls (PRD 4.5)
      answerRevealTries: 2, // 1 to 3
      probeInputMode: "both", // voice | tap | both
      frustrationGuard: true,
      reasoningVisibility: true,
      lastSyncTimestamp: new Date().toISOString()
    },
    child_maya: {
      dailyTimeLimitMins: 60,
      timeSpentTodayMins: 45,
      bedtimeSchedule: { enabled: true, start: "21:00", end: "07:00" },
      pausedNow: false,
      subjectAllowlist: ["Math", "Physics", "English Literature"],
      contentLevel: "Ages 10-12",
      answerRevealTries: 2,
      probeInputMode: "voice",
      frustrationGuard: true,
      reasoningVisibility: true,
      lastSyncTimestamp: new Date().toISOString()
    }
  },
  privacyConsent: {
    child_leo: {
      voiceDataStore: true,
      cameraExpressionStore: false,
      storeChildReasoning: true,
      aiModelImprovement: false
    }
  },
  learnerModels: {
    child_leo: {
      streakDays: 5,
      selfCorrectionRate: 78, // % wrong answers fixed after Wini's probe
      topicsCoveredToday: ["Fractions & Decimals", "Gravity & Falling Objects", "Word Roots"],
      mastery: [
        { subject: "Mathematics", score: 84, trend: "+4%" },
        { subject: "Science & Nature", score: 72, trend: "+8%" },
        { subject: "Language & Logic", score: 90, trend: "+2%" }
      ],
      misconceptions: [
        {
          id: "misc_101",
          subject: "Physics",
          concept: "Gravity & Floating in Water",
          date: "Today, 4:15 PM",
          questionAsked: "Why do heavy ships float while small rocks sink?",
          childChoice: "Option B: Ships have air inside, so gravity turns off for them.",
          childStatedReason: "I picked B because when I go underwater in the pool I feel weightless so gravity stops working underwater.",
          parentTip: "Explain buoyancy as water pushing up against gravity, rather than gravity turning off underwater."
        },
        {
          id: "misc_102",
          subject: "Mathematics",
          concept: "Fraction Addition",
          date: "Yesterday, 5:30 PM",
          questionAsked: "What is 1/2 + 1/4?",
          childChoice: "Option C: 2/6",
          childStatedReason: "I added 1+1 on top to get 2 and 2+4 on bottom to get 6.",
          parentTip: "Remind Leo to make denominators equal before adding top numbers. Use pizza slices as a visual example!"
        }
      ],
      recentSessions: [
        {
          id: "sess_301",
          date: "Oct 4, 2026",
          duration: "28 mins",
          subject: "Science",
          triesToCorrectAvg: 1.4,
          actionMix: { explain: "30%", hint: "40%", practice: "20%", assess: "10%" }
        },
        {
          id: "sess_300",
          date: "Oct 3, 2026",
          duration: "35 mins",
          subject: "Math",
          triesToCorrectAvg: 1.2,
          actionMix: { explain: "20%", hint: "50%", practice: "30%", assess: "0%" }
        }
      ]
    }
  }
};

// WebSocket connection for real-time Wini Robot sync (<30s PRD requirement)
let connectedRobots = [];

wss.on('connection', (ws) => {
  console.log('[WebSocket] Robot client connected');
  connectedRobots.push(ws);

  // Send initial sync state
  ws.send(JSON.stringify({
    type: 'SYNC_INIT',
    controls: state.controls.child_leo,
    timestamp: new Date().toISOString()
  }));

  ws.on('close', () => {
    connectedRobots = connectedRobots.filter(client => client !== ws);
    console.log('[WebSocket] Robot client disconnected');
  });
});

function broadcastControlsUpdate(childId, controls) {
  const payload = JSON.stringify({
    type: 'CONTROLS_UPDATED',
    childId: childId,
    controls: controls,
    timestamp: new Date().toISOString()
  });

  connectedRobots.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(payload);
    }
  });
}

// REST Endpoints
app.get('/api/health', (req, res) => {
  res.json({ status: "online", timestamp: new Date().toISOString(), service: "ROAVAI Cloud Tutor Parent Backend" });
});

// Auth & Consent
app.post('/api/auth/login', (req, res) => {
  const { email } = req.body;
  res.json({
    success: true,
    token: "mock-jwt-token-12345",
    parent: state.parent
  });
});

app.post('/api/consent', (req, res) => {
  const { consentRecorded, method } = req.body;
  state.parent.consentRecorded = consentRecorded;
  state.parent.consentTimestamp = new Date().toISOString();
  state.parent.consentMethod = method || "DIGITAL_PARENTAL_CONSENT";

  res.json({
    success: true,
    consentRecorded: state.parent.consentRecorded,
    timestamp: state.parent.consentTimestamp
  });
});

// Children Management
app.get('/api/children', (req, res) => {
  res.json({ children: state.children });
});

app.post('/api/children', (req, res) => {
  if (!state.parent.consentRecorded) {
    return res.status(403).json({ error: "FR-1: Parental consent required before adding child profile." });
  }

  if (state.children.length >= 4) {
    return res.status(400).json({ error: "Maximum limit of 4 child profiles reached." });
  }

  const { name, age, grade, curriculum, language } = req.body;
  const newId = `child_${Date.now()}`;
  const newChild = {
    id: newId,
    name: name || "Learner",
    age: Number(age) || 8,
    grade: grade || "3rd Grade",
    curriculum: curriculum || "General Elementary",
    language: language || "English",
    avatar: "🌟",
    winiPaired: false,
    winiDeviceId: null,
    winiStatus: "offline"
  };

  state.children.push(newChild);

  // Initialize controls and learner model for new child
  state.controls[newId] = {
    dailyTimeLimitMins: 45,
    timeSpentTodayMins: 0,
    bedtimeSchedule: { enabled: true, start: "20:00", end: "07:00" },
    pausedNow: false,
    subjectAllowlist: ["Math", "Science"],
    contentLevel: `Ages ${age-1}-${age+1}`,
    answerRevealTries: 2,
    probeInputMode: "both",
    frustrationGuard: true,
    reasoningVisibility: true,
    lastSyncTimestamp: new Date().toISOString()
  };

  state.learnerModels[newId] = {
    streakDays: 0,
    selfCorrectionRate: 100,
    topicsCoveredToday: [],
    mastery: [{ subject: "General Knowledge", score: 50, trend: "0%" }],
    misconceptions: [],
    recentSessions: []
  };

  res.json({ success: true, child: newChild });
});

// Pairing
app.post('/api/pairing/qr', (req, res) => {
  const { childId, qrCodeData } = req.body;
  if (!qrCodeData || !qrCodeData.startsWith("WINI-QR-")) {
    return res.status(400).json({ error: "FR-2: Invalid QR code scanned. Make sure Wini displays a valid setup QR code." });
  }

  const deviceId = qrCodeData.replace("WINI-QR-", "WINI-ROBOT-");
  const child = state.children.find(c => c.id === childId);
  if (child) {
    child.winiPaired = true;
    child.winiDeviceId = deviceId;
    child.winiStatus = "online";
  }

  res.json({
    success: true,
    message: "Wini robot successfully paired!",
    deviceId: deviceId,
    pairedAt: new Date().toISOString()
  });
});

// Learner Model & Dashboard Data
app.get('/api/learner-model/:childId', (req, res) => {
  const { childId } = req.params;
  const model = state.learnerModels[childId] || {
    streakDays: 1,
    selfCorrectionRate: 80,
    topicsCoveredToday: ["Introductory Science"],
    mastery: [{ subject: "Science", score: 65, trend: "+5%" }],
    misconceptions: [],
    recentSessions: []
  };

  // Check consent for reasoning visibility (FR-7)
  const consent = state.privacyConsent[childId] || { storeChildReasoning: true };
  const sanitizedModel = { ...model };

  if (!consent.storeChildReasoning) {
    sanitizedModel.misconceptions = sanitizedModel.misconceptions.map(m => ({
      ...m,
      childStatedReason: "[Consent Disabled: Storing child reasoning is toggled off in Privacy settings]"
    }));
  }

  res.json(sanitizedModel);
});

// Usage & Tutoring Controls
app.get('/api/controls/:childId', (req, res) => {
  const { childId } = req.params;
  const childControls = state.controls[childId] || state.controls.child_leo;
  res.json(childControls);
});

app.post('/api/controls/:childId', (req, res) => {
  const { childId } = req.params;
  const newRules = req.body;

  if (!state.controls[childId]) {
    state.controls[childId] = {};
  }

  state.controls[childId] = {
    ...state.controls[childId],
    ...newRules,
    lastSyncTimestamp: new Date().toISOString()
  };

  // Update robot status if pausedNow changed
  const child = state.children.find(c => c.id === childId);
  if (child && child.winiPaired) {
    child.winiStatus = state.controls[childId].pausedNow ? "paused" : "online";
  }

  // Broadcast to connected robot via WebSocket (sync within <30 seconds)
  broadcastControlsUpdate(childId, state.controls[childId]);

  res.json({
    success: true,
    message: "Controls updated and synced to Wini",
    syncTimestamp: state.controls[childId].lastSyncTimestamp,
    controls: state.controls[childId]
  });
});

// Privacy & Data
app.get('/api/privacy/export/:childId', (req, res) => {
  const { childId } = req.params;
  const exportPayload = {
    exportDate: new Date().toISOString(),
    parent: state.parent,
    child: state.children.find(c => c.id === childId),
    controls: state.controls[childId],
    privacySettings: state.privacyConsent[childId],
    learnerModel: state.learnerModels[childId]
  };

  res.json(exportPayload);
});

app.delete('/api/privacy/delete/:childId', (req, res) => {
  const { childId } = req.params;
  // FR-9: Delete child profile and schedule data purge within 30 days
  state.children = state.children.filter(c => c.id !== childId);
  delete state.controls[childId];
  delete state.learnerModels[childId];
  delete state.privacyConsent[childId];

  res.json({
    success: true,
    message: "FR-9: Child profile deleted. Learner history and stored reasoning scheduled for deletion within 30 days.",
    deletionConfirmedAt: new Date().toISOString()
  });
});

server.listen(PORT, () => {
  console.log(`[ROAVAI Mock Server] Listening on http://localhost:${PORT}`);
  console.log(`[WebSocket] Live robot sync stream ready on ws://localhost:${PORT}`);
});
