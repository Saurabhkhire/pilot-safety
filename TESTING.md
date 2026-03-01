# Testing EngageIQ Flight Deck locally

## 1. Minimal run (no Ollama, no cameras)

You can run and test the full HUD with **mock data** only.

### Start backend

```bash
cd engageiq-flight/backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

- If port 8000 is in use: `uvicorn main:app --host 0.0.0.0 --port 8001`  
  Then in `frontend/vite.config.ts` set proxy target to `http://localhost:8001`.

### Start frontend

```bash
cd engageiq-flight/frontend
npm install
npm run dev
```

- Open **http://localhost:5173**
- You should see the HUD; connection indicator will show **Live** when the WebSocket is connected.
- With no Ollama/cameras, the backend uses a default **ALERT** state, so PSI stays high (green).

---

## 2. Test scenarios (inject mock data)

Without real cameras or Ollama, drive the UI with predefined scenarios.

**Available scenarios:** `nominal` | `drowsy` | `critical` | `landing_bounce` | `cockpit_errors`

### From browser or curl

```bash
# List scenarios
curl http://localhost:8000/test/scenarios

# Inject a scenario (HUD updates on next WebSocket tick, ~500ms)
curl -X POST "http://localhost:8000/test/inject?scenario=nominal"
curl -X POST "http://localhost:8000/test/inject?scenario=drowsy"
curl -X POST "http://localhost:8000/test/inject?scenario=critical"
curl -X POST "http://localhost:8000/test/inject?scenario=landing_bounce"
curl -X POST "http://localhost:8000/test/inject?scenario=cockpit_errors"
```

### What to check

| Scenario        | Expected |
|-----------------|----------|
| **nominal**     | PSI ~95+, green, NOMINAL |
| **drowsy**      | PSI drops (e.g. 50–70), WARNING, agent actions like `trigger_alert(WARNING, ...)` |
| **critical**    | PSI low (e.g. &lt;35), CRITICAL, red banner, `notify_copilot` in agent feed |
| **landing_bounce** | Landing report: score 10, 4 bounces, bounce timeline |
| **cockpit_errors**  | Procedural deductions, PSI lower, error log shows gear/checklist items |

---

## 3. REST checks (no frontend)

```bash
# Health
curl http://localhost:8000/health

# Current state (after any inject)
curl http://localhost:8000/state
```

---

## 4. Test with video file (instead of camera)

1. Get a yawning/drowsy face video (MP4, AVI, MOV, WebM, MKV). See `backend/test_videos/README.md` for sources.
2. Open the **Simulator** panel (right side).
3. Click **Upload video** and select your file.
4. The backend reads frames from the video instead of the camera (loops when done).
5. Click **Clear** to switch back to live camera.

---

## 5. With Ollama (real models)

1. Install and run [Ollama](https://ollama.com), then:
   ```bash
   ollama pull gemma3n
   ollama pull functiongemma
   ```
2. Start backend + frontend as above.
3. **With webcam:** Backend will use camera index 0 for face frames and call Gemma 3n for perception (and FunctionGemma for actions).  
   **Without webcam:** Perception stays in default ALERT state; you can still use `/test/inject` to simulate.

---

## 6. With a replay file (cockpit + phase)

1. Create a JSON file, e.g. `backend/replay.json`:
   ```json
   [
     {"ts": 0, "phase": "cruise"},
     {"ts": 60, "phase": "approach"},
     {"ts": 120, "phase": "landing", "event": "cockpit_error", "errors": [{"type": "omission", "description": "Gear down late", "ts": 120}]}
   ]
   ```
2. Set env and run backend:
   ```bash
   set REPLAY_JSON=replay.json
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
   (Replay loop would need to be started from `sim_bridge`; currently inject is the main way to test cockpit errors.)

---

## 7. Quick test flow

1. Start backend and frontend.
2. Open http://localhost:5173 — confirm **Live** and PSI ring.
3. Run: `curl -X POST "http://localhost:8000/test/inject?scenario=drowsy"`.
4. Watch PSI and alert level change, and agent feed show actions.
5. Run: `curl -X POST "http://localhost:8000/test/inject?scenario=critical"` — red CRITICAL banner.
6. Run: `curl -X POST "http://localhost:8000/test/inject?scenario=landing_bounce"` — landing report and score 10.
7. Run: `curl -X POST "http://localhost:8000/test/inject?scenario=nominal"` — back to green.

Done. You’ve tested the pipeline locally without Ollama or cameras.
