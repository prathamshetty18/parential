# PRD: ROAVAI Parental Control App (Android)

| | |
|---|---|
| **Product** | Parent companion app for Wini, the Cloud Tutor desktop robot |
| **Platform** | Android (phone) |
| **Status** | Draft v0.3 (trimmed) |
| **Note** | Items marked **[ASSUMPTION]** need confirmation. |

---

## 1. Overview

ROAVAI builds Wini, a desktop robot that runs Cloud Tutor, a self-improving personal AI tutor for children. Cloud Tutor models each learner (mastery, misconceptions, curiosity, history), picks a teaching action, generates content, and updates the learner model after each response.

**Probe-first tutoring.** Wini does not hand over answers. When a child picks a wrong MCQ option, Wini asks why they chose it, finds the misconception, gives a targeted hint, and lets them retry.

The Parental Control App lets parents see what their child is learning (including the child's own reasoning behind mistakes) and control how Wini is used.

**[ASSUMPTION]** "Parental control" means controlling and monitoring Wini, not blocking apps on the child's devices.

## 2. Goals and Non-Goals

### Goals
1. Pair Wini and create a child profile in under 5 minutes.
2. Show clear progress from the Cloud Tutor learner model.
3. Let parents set usage limits and tutoring style.
4. Give parents full control of their child's data.

### Non-Goals (v1)
- Child-facing UI (lives on Wini)
- Device-level screen-time control
- iOS app, school/teacher dashboards, in-app hardware purchase

## 3. User

**Parent or guardian.** Wants to know if the child is learning, limit usage, and trust the data handling. The child never uses this app.

## 4. Features

Priority: **P0** = launch blocker, **P1** = launch target.

### 4.1 Account and Onboarding (P0)
- Sign up and log in (email, Google).
- Parental consent step before any child profile is created.
- Child profile: name or nickname, age, grade, curriculum, language. **[ASSUMPTION]** Up to 4 children.
- App lock: PIN or biometric, so the child cannot open the app.

### 4.2 Robot Pairing (P0)
- Pair Wini by QR code.
- Wi-Fi setup from the phone **[ASSUMPTION: depends on robot firmware]**.
- Assign Wini to a child; show connection status; unpair.

### 4.3 Progress Dashboard (P0)
- Home summary: time today, topics covered, streak.
- Mastery per subject and topic.
- Misconceptions: each shows the child's own stated reason (for example, "picked B because they thought X") and a short parent tip.
- Self-correction rate: share of wrong answers the child fixed after the probe.
- 7 and 30 day trends.
- Session list: date, duration, subject, tries to correct, action mix (explain, hint, practice, assess, probe).

### 4.4 Usage Controls (P0)
- Daily time limit per child.
- Schedule and bedtime lock.
- Pause Wini now.
- Subject allow-list.
- Content level (age band).
- Controls sync to Wini within 30 s when online; Wini keeps enforcing last rules offline.

### 4.5 Probe-First Tutoring Controls (P0)
How it works on Wini: child asks, gets an MCQ, picks an option. Correct: move on. Wrong: Wini asks why, child explains (voice or tap), tutor finds the misconception, gives a hint, child retries.

- **Answer-reveal rule:** parent sets wrong tries before Wini gives the answer. **[ASSUMPTION]** Default 2, range 1 to 3. Wini always reveals eventually; a child is never stuck.
- **Probe input mode:** voice, tap, or both.
- **Frustration guard:** after repeated wrong answers or detected frustration, Wini switches from probing to hint or explanation. On by default.
- **Reasoning visibility:** parents see a summary of the child's reasoning. Raw audio is never shown.

### 4.6 Alerts (P1)
- Weekly learning report.
- Daily limit reached.
- Child struggling on the same concept.
- Wini offline.
- Per-alert on/off and quiet hours.

### 4.7 Privacy and Data (P0)
- Separate consent toggles: voice, camera/expression, storing the child's reasoning from probe questions, use of data to improve models.
- Export child data.
- Delete child data and account; deletion also removes stored reasoning and misconception history.
- Screen explaining what Wini collects and why.

## 5. Key User Flows

**Onboarding:** Sign up → consent → add child → pair Wini (QR) → Wi-Fi → set time limit.

**Daily check-in:** Open app (PIN) → Home → Misconceptions → read child's reason and tip.

**Set tutoring style:** Controls → child → Tutoring style → tries before answer, probe input mode → Save → "Applied on Wini".

**Child-side probe loop (runs on Wini):** MCQ → wrong → "why did you pick that?" → child explains → hint → retry → learner model updated.

## 6. Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-1 | No child profile until parental consent is recorded with timestamp and method. | P0 |
| FR-2 | Pairing completes via QR with clear errors (invalid code, already paired, no Wi-Fi). | P0 |
| FR-3 | Dashboard loads cached data in under 1 s and refreshes in the background. | P0 |
| FR-4 | Control changes reach Wini within 30 s online; Wini enforces last rules offline. | P0 |
| FR-5 | Parent sets tries (1 to 3) before answer reveal; Wini always reveals after the limit. | P0 |
| FR-6 | Misconception entries show the child's reason in summary form and a parent tip. | P0 |
| FR-7 | Child's reasoning is stored and shown only with its consent toggle on. | P0 |
| FR-8 | Frustration guard is on by default and switches Wini from probe to hint or explanation. | P0 |
| FR-9 | Deleting a child profile removes learner data within 30 days and confirms to the parent. | P0 |
| FR-10 | App requires PIN or biometric after backgrounding over 1 minute. | P1 |

## 7. Technical Approach

**Android:** Kotlin, Jetpack Compose, MVVM, Hilt, Coroutines/Flow, Retrofit, Room, DataStore, FCM, CameraX + ML Kit for QR. Min SDK 26.
