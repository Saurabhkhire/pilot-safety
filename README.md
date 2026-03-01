# EngageIQ Flight Deck

**Real-time pilot behavioral safety monitoring** — Google DeepMind × InstaLILY On-Device AI Hackathon.

Two camera feeds + cockpit data → **Pilot Safety Index (PSI, 0–100)** and escalating safety interventions. **Fully on-device** — no cloud inference.

---

## Tech stack

| Layer | Stack |
|-------|--------|
| Models | Gemma 3n E4B (perception + landing), PaliGemma 2 (pilot state), FunctionGemma 270M (action agent) via **Ollama** |
| Backend | Python 3.11, FastAPI, WebSocket @ 2Hz, OpenCV, SQLite |
| Frontend | React 18, TypeScript, Vite, Tailwind, Recharts |
| Sim | X-Plane xpc or pre-recorded JSON replay |

---

## Why on-device (for judges)

1. **Privacy / security** — Pilot biometric video cannot leave the aircraft.
2. **Latency** — Alerts must be &lt;500ms; cloud round-trip at cruise (satellite) is 600–800ms+.
3. **Offline** — Oceanic routes have no connectivity for hours.
4. **Economics** — Continuous camera feed is impractical with per-call API pricing.

---

## Quick start

### 1. Ollama

```bash
# Install Ollama, then:
ollama pull gemma3n
ollama pull functiongemma
# Optional: build from ollama/modelfiles/
```

### 2. Backend

```bash
cd engageiq-flight/backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. Frontend

```bash
cd engageiq-flight/frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The HUD consumes the WebSocket at `/ws` (proxied to backend 8000).

### 4. (Optional) Fine-tuning

- **PaliGemma pilot state**: `python finetune/train_paligemma_pilot.py` (after preparing NTHU/UTA dataset).
- **FunctionGemma actions**: `python finetune/train_functiongemma_actions.py` (generates synthetic dataset stub).

---

## Project layout

```
engageiq-flight/
├── backend/          # FastAPI, agents, scoring, cameras, cockpit, db
├── frontend/         # React HUD (PSI ring, signals, agent feed, alerts)
├── finetune/         # LoRA / full fine-tune scripts + dataset stubs
├── ollama/            # Modelfiles for Gemma 3n and FunctionGemma
└── README.md
```

---

## Three agents

| Agent | Model | Input | Output |
|-------|--------|--------|--------|
| **PerceptionAgent** | Gemma 3n | Face frame (Cam A) + phase | `pilot_state` JSON (state, perclos_est, yawn, head_drop, gaze_off, …) |
| **ActionAgent** | FunctionGemma 270M | `pilot_state` + context | Function calls: `trigger_alert`, `notify_copilot`, `suggest_rest_protocol`, etc. |
| **LandingAgent** | Gemma 3n | External/belly frame (Cam B) in approach/landing | `landing_report` (bounce_count, on_centerline, contact_type, score) |

---

## PSI scoring (0–100)

- **Fatigue**: PERCLOS, yawn count, micro-sleep (CRITICAL) events.
- **Attention**: Head drop, gaze-off-instruments.
- **Procedural**: Cockpit error points (wrong_button, omission, commission, reversal, sequence_error).
- **Landing**: Penalty if last landing score &lt; 40.

Alert bands: **85–100** NOMINAL → **70–84** MONITOR → **55–69** CAUTION → **35–54** WARNING → **0–34** CRITICAL.

---

## Demo script (for judges)

1. **Cold HUD** — PSI 95, green, NOMINAL (simulated alert cruise).
2. **Drowsy video** (e.g. NTHU via Cam A) — PSI drops; Agent feed shows `trigger_alert(WARNING, …)` and `suggest_rest_protocol(15)`.
3. **4-bounce landing** (Cam B) — LandingAgent score ~10, “runway excursion risk”.
4. **Cockpit error** (missed gear-down) — Procedural deduction, PSI drops.
5. **PSI CRITICAL** — Red banner, `notify_copilot()`.
6. **Offline** — Turn off WiFi; system keeps running.

---

## Safety note

This is a **pilot decision-support prototype**. Real aircraft deployment requires DO-178C software certification and FAA/EASA approval.
