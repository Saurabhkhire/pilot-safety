# EngageIQ Flight Deck — Project Summary

## Project Description

EngageIQ Flight Deck is a **real-time pilot behavioral safety monitoring system** that computes a live **Pilot Safety Index (PSI, 0–100)** from two camera feeds and cockpit data, triggering escalating safety interventions. Built for the Google DeepMind × InstaLILY On-Device AI Hackathon, the system runs **fully on-device** via Ollama — no cloud inference. Camera 1 captures the pilot's face for fatigue detection (PERCLOS, yawning, head drop, gaze); Camera 2 captures external/belly views for landing quality analysis. A composite PSI engine aggregates perception, attention, procedural, and landing components, and a FunctionGemma-based ActionAgent autonomously calls safety functions (trigger_alert, notify_copilot, suggest_rest_protocol, etc.) based on pilot state.

---

## Architecture

```
CAMERA 1 (Pilot Face)       CAMERA 2 (External/Belly)     X-Plane / Replay
         │                            │                           │
         ▼                            ▼                           ▼
   OpenCV / Video              OpenCV / Video              sim_bridge.py
         │                            │                           │
         ▼                            ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         OLLAMA (on-device)                               │
│                                                                         │
│  PerceptionAgent         LandingAgent         ActionAgent               │
│  Gemma 3n E4B              Gemma 3n E4B       FunctionGemma 270M        │
│  + PaliGemma LoRA          (approach/landing) fine-tuned                 │
│                                                                         │
│  → pilot_state JSON       → landing_report    → function calls          │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                           PSI Scoring Engine
                           psi_engine.py
                                      │
                           WebSocket @ 2Hz
                                      │
                           ┌──────────▼──────────┐
                           │   React HUD         │
                           │   PSI Ring          │
                           │   Signal Cards      │
                           │   Agent Feed        │
                           │   Landing Report    │
                           │   Alert Banner      │
                           └─────────────────────┘
```

- **Backend:** FastAPI + WebSocket (2Hz), OpenCV cameras, SQLite logging
- **Frontend:** React 18 + TypeScript + Vite, Tailwind, Recharts
- **Models:** Gemma 3n (perception, landing), FunctionGemma 270M (actions)

---

## User Flow

1. **Start system** — Backend and frontend run locally; WebSocket connects.
2. **Feed sources** — User uploads videos (Cam 1: pilot face, Cam 2: landing/takeoff) or uses live cameras.
3. **Perception loop** — Every 2s, PerceptionAgent sends a face frame to Gemma 3n → receives pilot_state (state, perclos, yawn, head_drop, gaze).
4. **Action loop** — FunctionGemma receives pilot_state → outputs function calls (trigger_alert, notify_copilot, etc.).
5. **PSI computation** — Backend aggregates rolling signals + cockpit errors + landing score → computes PSI 0–100.
6. **HUD update** — WebSocket streams JSON to React HUD; PSI ring, signals, agent feed, landing report, alert banner update in real time.
7. **Escalation** — As PSI drops (WARNING → CRITICAL), alerts escalate; ActionAgent autonomously notifies copilot, suggests rest, requests ATC advisory.

---

## Implementation

| Component | Technology | Notes |
|-----------|------------|-------|
| **PerceptionAgent** | Gemma 3n via Ollama `/api/generate` | Face frame → JSON (state, perclos_est, yawn, head_drop, gaze_off) |
| **ActionAgent** | FunctionGemma 270M | pilot_state → parsed function call strings; rule-based fallback if model unavailable |
| **LandingAgent** | Gemma 3n | External frame in approach/landing → landing_report JSON |
| **PSI Engine** | `psi_engine.py` | Composite score from perclos, yawns, critical events, head drop, gaze, cockpit points, landing penalty |
| **Cameras** | OpenCV `VideoCapture` | Supports device indices (0, 1) or uploaded video files (MP4, AVI, MOV) |
| **Cockpit** | `sim_bridge.py`, `error_classifier.py` | X-Plane xpc or JSON replay; 5 error types (wrong_button, omission, commission, reversal, sequence_error) |
| **Frontend** | React, Tailwind, Recharts | PSIRing, SignalGrid, VitalsStrip, LandingReport, AgentFeed, ErrorLog, AlertBanner, PSITimeline |
| **Video / Simulator** | Hideable panels | Upload Cam 1/Cam 2; inject 20 test scenarios (nominal, warning, critical, takeoff/landing, cockpit errors) |

---

## Key Claims (required, one per line)

All inference runs on-device; no cloud API calls.
Pilot biometric video never leaves the aircraft.
Alert latency &lt;500ms; cloud round-trip at cruise (satellite) is 600–800ms+.
System operates fully offline; oceanic routes have no connectivity for hours.
Gemma 3n reasons over face frames for fatigue; not hardcoded thresholds.
FunctionGemma autonomously decides alerts and co-pilot notification; rules are not hardcoded.
Fine-tuned PaliGemma and FunctionGemma improve pilot-state and action-call accuracy.
PSI aggregates fatigue, attention, procedural, and landing components into a single 0–100 index.
Escalating alert bands: NOMINAL → MONITOR → CAUTION → WARNING → CRITICAL.
Prototype for pilot decision-support; real deployment requires DO-178C and FAA/EASA approval.
