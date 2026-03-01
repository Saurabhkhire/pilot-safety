"""
EngageIQ Flight Deck — FastAPI app + WebSocket hub.
Streams PSI JSON to frontend at 2Hz. All inference on-device via Ollama.
"""
from __future__ import annotations

import asyncio
import json
import time
from contextlib import asynccontextmanager
from typing import Any

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import config
from db.event_logger import init_db
from scoring.psi_engine import compute_psi
from scoring.alert_manager import get_alert_for_psi


# In-memory state (in production, use a proper state store)
_current_state: dict[str, Any] = {
    "ts": 0.0,
    "psi": 100.0,
    "phase": "cruise",
    "pilot_state": None,
    "signals": {},
    "cockpit_errors": [],
    "landing": None,
    "alert": None,
    "agent_actions": [],
}


async def _run_perception_loop() -> None:
    """Background: run perception agent and update state (uses camera frame when available)."""
    from agents.perception_agent import PerceptionAgent
    from cameras.camera_manager import get_frame_face
    agent = PerceptionAgent()
    while True:
        try:
            phase = _current_state.get("phase", "cruise")
            frame_b64 = get_frame_face()  # None if no camera
            state = await agent.run_once(phase=phase, frame_b64=frame_b64)
            if state:
                _current_state["pilot_state"] = state
                _current_state["ts"] = time.time()
                # Update rolling signals for PSI (stub counts; in production aggregate over windows)
                sig = _current_state.setdefault("signals", {})
                if state.get("yawn"):
                    sig["yawn_count_10m"] = sig.get("yawn_count_10m", 0) + 1
                if state.get("head_drop"):
                    sig["head_drop_count_30m"] = sig.get("head_drop_count_30m", 0) + 1
                if state.get("gaze_off_instruments"):
                    sig["gaze_off_pct"] = min(100, sig.get("gaze_off_pct", 0) + 5)
                if state.get("state") == "CRITICAL":
                    sig["critical_events_1h"] = sig.get("critical_events_1h", 0) + 1
        except Exception as e:
            _current_state["pilot_state"] = {
                "state": "ALERT",
                "perclos_est": 0.0,
                "yawn": False,
                "head_drop": False,
                "gaze_off_instruments": False,
                "confidence": 0.0,
                "reason": str(e),
            }
        await asyncio.sleep(1.0 / config.psi_poll_hz)


async def _run_action_loop() -> None:
    """Background: run action agent when pilot_state updates (stub → replace with real)."""
    from agents.action_agent import ActionAgent
    agent = ActionAgent()
    while True:
        try:
            if _current_state.get("pilot_state"):
                actions = await agent.run_once(_current_state["pilot_state"], _current_state.get("phase", "cruise"))
                _current_state["agent_actions"] = actions or []
        except Exception:
            _current_state["agent_actions"] = []
        await asyncio.sleep(0.5)


def _build_psi_payload() -> dict[str, Any]:
    """Build full WebSocket payload from current state + PSI engine."""
    window = {
        "perclos_est": 0.0,
        "yawn_count_10m": 0,
        "critical_events_1h": 0,
        "head_drop_count_30m": 0,
        "gaze_off_pct": 0.0,
        "cockpit_error_points_session": 0,
        "last_landing_score": _current_state.get("landing", {}).get("score", 100) if _current_state.get("landing") else 100,
    }
    ps = _current_state.get("pilot_state")
    if ps:
        window["perclos_est"] = ps.get("perclos_est", 0) or 0
        window["yawn_count_10m"] = _current_state.get("signals", {}).get("yawn_count_10m", 0)
        window["critical_events_1h"] = _current_state.get("signals", {}).get("critical_events_1h", 0)
        window["head_drop_count_30m"] = _current_state.get("signals", {}).get("head_drop_count_30m", 0)
        window["gaze_off_pct"] = _current_state.get("signals", {}).get("gaze_off_pct", 0.0)
    window["cockpit_error_points_session"] = sum(
        e.get("points_deducted", 0) for e in _current_state.get("cockpit_errors", [])
    )
    psi = compute_psi(window)
    _current_state["psi"] = psi
    alert = get_alert_for_psi(psi)
    _current_state["alert"] = alert
    return {
        "ts": _current_state["ts"] or time.time(),
        "psi": psi,
        "phase": _current_state.get("phase", "cruise"),
        "pilot_state": _current_state.get("pilot_state"),
        "signals": _current_state.get("signals", {}),
        "cockpit_errors": _current_state.get("cockpit_errors", []),
        "landing": _current_state.get("landing"),
        "alert": alert,
        "agent_actions": _current_state.get("agent_actions", []),
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background tasks and DB."""
    await init_db()
    task_p = asyncio.create_task(_run_perception_loop())
    task_a = asyncio.create_task(_run_action_loop())
    yield
    task_p.cancel()
    task_a.cancel()
    try:
        await task_p
        await task_a
    except asyncio.CancelledError:
        pass


app = FastAPI(title="EngageIQ Flight Deck", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket broadcast
_ws_clients: list[WebSocket] = []


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    _ws_clients.append(websocket)
    try:
        while True:
            payload = _build_psi_payload()
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(config.ws_interval_sec)
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in _ws_clients:
            _ws_clients.remove(websocket)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "message": "EngageIQ Flight Deck — on-device only"}


@app.get("/state")
def state() -> dict[str, Any]:
    """Current state snapshot (for debugging)."""
    return _build_psi_payload()


# ---------------------------------------------------------------------------
# Local testing: inject scenarios without Ollama/cameras
# ---------------------------------------------------------------------------

TEST_SCENARIOS: dict[str, dict[str, Any]] = {
    # --- NOMINAL ---
    "nominal": {
        "pilot_state": {"state": "ALERT", "perclos_est": 2.0, "yawn": False, "head_drop": False, "gaze_off_instruments": False, "confidence": 0.95, "reason": "Pilot alert, eyes on instruments"},
        "signals": {"yawn_count_10m": 0, "head_drop_count_30m": 0, "gaze_off_pct": 2.0, "critical_events_1h": 0},
        "phase": "cruise", "cockpit_errors": [], "landing": None,
        "agent_actions": [],
    },
    # --- WARNING (fatigue onset, gaze, yawn) ---
    "drowsy": {
        "pilot_state": {"state": "DROWSY", "perclos_est": 18.0, "yawn": True, "head_drop": False, "gaze_off_instruments": True, "confidence": 0.88, "reason": "Elevated perclos, gaze drifting right"},
        "signals": {"yawn_count_10m": 3, "head_drop_count_30m": 1, "gaze_off_pct": 18.0, "critical_events_1h": 0},
        "phase": "cruise", "cockpit_errors": [], "landing": None,
        "agent_actions": ['trigger_alert(WARNING, "Drowsiness detected")', "suggest_rest_protocol(15)"],
    },
    "fatigue_onset": {
        "pilot_state": {"state": "FATIGUED", "perclos_est": 12.0, "yawn": False, "head_drop": False, "gaze_off_instruments": True, "confidence": 0.85, "reason": "Fatigue onset, perclos rising"},
        "signals": {"yawn_count_10m": 1, "head_drop_count_30m": 0, "gaze_off_pct": 15.0, "critical_events_1h": 0},
        "phase": "cruise", "cockpit_errors": [], "landing": None,
        "agent_actions": ["log_fatigue_event(perclos_elevated, severity=2)", 'trigger_alert(WARNING, "Fatigue onset")'],
    },
    "gaze_drift": {
        "pilot_state": {"state": "FATIGUED", "perclos_est": 8.0, "yawn": False, "head_drop": False, "gaze_off_instruments": True, "confidence": 0.9, "reason": "Gaze drifting left of instruments"},
        "signals": {"yawn_count_10m": 0, "head_drop_count_30m": 1, "gaze_off_pct": 22.0, "critical_events_1h": 0},
        "phase": "cruise", "cockpit_errors": [], "landing": None,
        "agent_actions": ['trigger_alert(WARNING, "Gaze deviation detected")'],
    },
    "yawn_series": {
        "pilot_state": {"state": "DROWSY", "perclos_est": 14.0, "yawn": True, "head_drop": False, "gaze_off_instruments": False, "confidence": 0.87, "reason": "Repeated yawning in cruise"},
        "signals": {"yawn_count_10m": 4, "head_drop_count_30m": 0, "gaze_off_pct": 8.0, "critical_events_1h": 0},
        "phase": "cruise", "cockpit_errors": [], "landing": None,
        "agent_actions": ['trigger_alert(WARNING, "Yawn frequency elevated")', "suggest_rest_protocol(20)"],
    },
    # --- CRITICAL (micro-sleep, head drop, extreme fatigue) ---
    "critical": {
        "pilot_state": {"state": "CRITICAL", "perclos_est": 32.0, "yawn": True, "head_drop": True, "gaze_off_instruments": True, "confidence": 0.9, "reason": "Micro-sleep risk, head drop detected"},
        "signals": {"yawn_count_10m": 5, "head_drop_count_30m": 4, "gaze_off_pct": 35.0, "critical_events_1h": 2},
        "phase": "cruise", "cockpit_errors": [], "landing": None,
        "agent_actions": ['trigger_alert(CRITICAL, "Pilot fatigue critical")', "notify_copilot(reason='Critical fatigue')"],
    },
    "micro_sleep": {
        "pilot_state": {"state": "CRITICAL", "perclos_est": 40.0, "yawn": True, "head_drop": True, "gaze_off_instruments": True, "confidence": 0.92, "reason": "Eyes closed >3s, head drop"},
        "signals": {"yawn_count_10m": 6, "head_drop_count_30m": 5, "gaze_off_pct": 50.0, "critical_events_1h": 3},
        "phase": "cruise", "cockpit_errors": [], "landing": None,
        "agent_actions": ['trigger_alert(CRITICAL, "Micro-sleep detected")', "notify_copilot(reason='Micro-sleep')", "request_atc_advisory(reason='Pilot incapacitation risk')"],
    },
    "head_drop_severe": {
        "pilot_state": {"state": "CRITICAL", "perclos_est": 28.0, "yawn": False, "head_drop": True, "gaze_off_instruments": True, "confidence": 0.88, "reason": "Severe head drop, eyelids drooping"},
        "signals": {"yawn_count_10m": 2, "head_drop_count_30m": 5, "gaze_off_pct": 40.0, "critical_events_1h": 1},
        "phase": "cruise", "cockpit_errors": [], "landing": None,
        "agent_actions": ['trigger_alert(CRITICAL, "Head drop severe")', "notify_copilot(reason='Head drop')"],
    },
    # --- TAKEOFF / LANDING ---
    "takeoff_smooth": {
        "pilot_state": {"state": "ALERT", "perclos_est": 1.0, "yawn": False, "head_drop": False, "gaze_off_instruments": False, "confidence": 0.95, "reason": "On takeoff"},
        "signals": {"yawn_count_10m": 0, "head_drop_count_30m": 0, "gaze_off_pct": 0, "critical_events_1h": 0},
        "phase": "takeoff", "cockpit_errors": [], "landing": None,
        "agent_actions": [],
    },
    "approach_nominal": {
        "pilot_state": {"state": "ALERT", "perclos_est": 3.0, "yawn": False, "head_drop": False, "gaze_off_instruments": False, "confidence": 0.92, "reason": "Stable approach"},
        "signals": {"yawn_count_10m": 0, "head_drop_count_30m": 0, "gaze_off_pct": 5.0, "critical_events_1h": 0},
        "phase": "approach", "cockpit_errors": [], "landing": None,
        "agent_actions": [],
    },
    "landing_bounce": {
        "pilot_state": {"state": "ALERT", "perclos_est": 1.0, "yawn": False, "head_drop": False, "gaze_off_instruments": False, "confidence": 0.9, "reason": "On approach"},
        "signals": {"yawn_count_10m": 0, "head_drop_count_30m": 0, "gaze_off_pct": 0, "critical_events_1h": 0},
        "phase": "landing", "cockpit_errors": [],
        "landing": {"score": 10, "bounce_count": 4, "contact_type": "bounce", "on_centerline": True, "events": [{"t_ms": 0, "type": "contact"}, {"t_ms": 900, "type": "bounce"}, {"t_ms": 2100, "type": "bounce"}, {"t_ms": 3400, "type": "bounce"}, {"t_ms": 4500, "type": "final_contact"}]},
        "agent_actions": ["log_fatigue_event(landing_hard, severity=3)"],
    },
    "landing_hard": {
        "pilot_state": {"state": "ALERT", "perclos_est": 2.0, "yawn": False, "head_drop": False, "gaze_off_instruments": False, "confidence": 0.9, "reason": "Touchdown"},
        "signals": {"yawn_count_10m": 0, "head_drop_count_30m": 0, "gaze_off_pct": 0, "critical_events_1h": 0},
        "phase": "landing", "cockpit_errors": [],
        "landing": {"score": 60, "bounce_count": 1, "contact_type": "hard", "on_centerline": True, "events": [{"t_ms": 0, "type": "contact"}]},
        "agent_actions": [],
    },
    "landing_greaser": {
        "pilot_state": {"state": "ALERT", "perclos_est": 1.0, "yawn": False, "head_drop": False, "gaze_off_instruments": False, "confidence": 0.95, "reason": "Smooth touchdown"},
        "signals": {"yawn_count_10m": 0, "head_drop_count_30m": 0, "gaze_off_pct": 0, "critical_events_1h": 0},
        "phase": "landing", "cockpit_errors": [],
        "landing": {"score": 100, "bounce_count": 0, "contact_type": "greaser", "on_centerline": True, "events": [{"t_ms": 0, "type": "contact"}]},
        "agent_actions": [],
    },
    "go_around": {
        "pilot_state": {"state": "ALERT", "perclos_est": 4.0, "yawn": False, "head_drop": False, "gaze_off_instruments": False, "confidence": 0.88, "reason": "Go-around initiated"},
        "signals": {"yawn_count_10m": 0, "head_drop_count_30m": 0, "gaze_off_pct": 5.0, "critical_events_1h": 0},
        "phase": "approach", "cockpit_errors": [], "landing": None,
        "agent_actions": [],
    },
    # --- COCKPIT ERRORS ---
    "cockpit_errors": {
        "pilot_state": {"state": "ALERT", "perclos_est": 3.0, "yawn": False, "head_drop": False, "gaze_off_instruments": False, "confidence": 0.9, "reason": "Nominal"},
        "signals": {"yawn_count_10m": 0, "head_drop_count_30m": 0, "gaze_off_pct": 5.0, "critical_events_1h": 0},
        "phase": "approach", "cockpit_errors": [
            {"ts": time.time() - 120, "type": "omission", "description": "Gear not down by 1000 ft AGL", "severity": 2, "points_deducted": 8},
            {"ts": time.time() - 60, "type": "sequence_error", "description": "Checklist out of order", "severity": 1, "points_deducted": 2},
        ], "landing": None,
        "agent_actions": [],
    },
    "cockpit_gear_omission": {
        "pilot_state": {"state": "ALERT", "perclos_est": 2.0, "yawn": False, "head_drop": False, "gaze_off_instruments": False, "confidence": 0.9, "reason": "Nominal"},
        "signals": {"yawn_count_10m": 0, "head_drop_count_30m": 0, "gaze_off_pct": 2.0, "critical_events_1h": 0},
        "phase": "approach", "cockpit_errors": [
            {"ts": time.time() - 90, "type": "omission", "description": "Landing gear not extended by 1000 ft AGL", "severity": 2, "points_deducted": 8},
        ], "landing": None,
        "agent_actions": ['trigger_alert(WARNING, "Gear omission")'],
    },
    "cockpit_wrong_button": {
        "pilot_state": {"state": "ALERT", "perclos_est": 1.0, "yawn": False, "head_drop": False, "gaze_off_instruments": False, "confidence": 0.92, "reason": "Nominal"},
        "signals": {"yawn_count_10m": 0, "head_drop_count_30m": 0, "gaze_off_pct": 0, "critical_events_1h": 0},
        "phase": "climb", "cockpit_errors": [
            {"ts": time.time() - 60, "type": "wrong_button", "description": "Selected wrong flap setting", "severity": 3, "points_deducted": 20},
        ], "landing": None,
        "agent_actions": ['trigger_alert(WARNING, "Wrong control selected")'],
    },
    "cockpit_reversal": {
        "pilot_state": {"state": "ALERT", "perclos_est": 2.0, "yawn": False, "head_drop": False, "gaze_off_instruments": False, "confidence": 0.88, "reason": "Nominal"},
        "signals": {"yawn_count_10m": 0, "head_drop_count_30m": 0, "gaze_off_pct": 3.0, "critical_events_1h": 0},
        "phase": "approach", "cockpit_errors": [
            {"ts": time.time() - 45, "type": "reversal", "description": "Throttle moved opposite to intended", "severity": 3, "points_deducted": 20},
        ], "landing": None,
        "agent_actions": ['trigger_alert(CRITICAL, "Control reversal")'],
    },
    "cockpit_sequence": {
        "pilot_state": {"state": "ALERT", "perclos_est": 1.0, "yawn": False, "head_drop": False, "gaze_off_instruments": False, "confidence": 0.9, "reason": "Nominal"},
        "signals": {"yawn_count_10m": 0, "head_drop_count_30m": 0, "gaze_off_pct": 0, "critical_events_1h": 0},
        "phase": "pre_takeoff", "cockpit_errors": [
            {"ts": time.time() - 30, "type": "sequence_error", "description": "Before-takeoff checklist out of order", "severity": 1, "points_deducted": 2},
            {"ts": time.time() - 15, "type": "sequence_error", "description": "Lights activated before transponder", "severity": 1, "points_deducted": 2},
        ], "landing": None,
        "agent_actions": [],
    },
    "cockpit_multi": {
        "pilot_state": {"state": "FATIGUED", "perclos_est": 10.0, "yawn": True, "head_drop": False, "gaze_off_instruments": True, "confidence": 0.85, "reason": "Fatigue + procedural errors"},
        "signals": {"yawn_count_10m": 2, "head_drop_count_30m": 1, "gaze_off_pct": 12.0, "critical_events_1h": 0},
        "phase": "approach", "cockpit_errors": [
            {"ts": time.time() - 120, "type": "omission", "description": "Autobrake not set", "severity": 2, "points_deducted": 8},
            {"ts": time.time() - 60, "type": "commission", "description": "Spoilers armed too early", "severity": 2, "points_deducted": 8},
        ], "landing": None,
        "agent_actions": ['trigger_alert(WARNING, "Fatigue and procedural errors")', "suggest_rest_protocol(15)"],
    },
}

# Log at startup so you can verify backend reloaded (should show 20 scenarios)
print(f"[EngageIQ] Loaded {len(TEST_SCENARIOS)} test scenarios: {sorted(TEST_SCENARIOS.keys())}")


def _apply_test_scenario(scenario: str) -> dict[str, Any]:
    """Apply scenario to state and return new payload."""
    if scenario not in TEST_SCENARIOS:
        return {"ok": False, "error": f"Unknown scenario. Use: {list(TEST_SCENARIOS.keys())}"}
    data = TEST_SCENARIOS[scenario]
    _current_state["ts"] = time.time()
    _current_state["pilot_state"] = data["pilot_state"]
    _current_state["signals"] = data["signals"]
    _current_state["phase"] = data["phase"]
    _current_state["cockpit_errors"] = data["cockpit_errors"]
    _current_state["landing"] = data["landing"]
    _current_state["agent_actions"] = data.get("agent_actions", [])
    return {"ok": True, "scenario": scenario, "state": _build_psi_payload()}


@app.post("/test/inject")
@app.get("/test/inject")
def test_inject(scenario: str = Query(..., description="Scenario name")) -> dict[str, Any]:
    """
    Inject a test scenario for local testing (no Ollama/cameras needed).
    scenario: nominal | drowsy | critical | landing_bounce | cockpit_errors
    """
    result = _apply_test_scenario(scenario)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "Bad request"))
    return result


@app.get("/test/scenarios")
def test_scenarios() -> dict[str, list[str]]:
    """List available test scenario names."""
    return {"scenarios": list(TEST_SCENARIOS.keys())}


ALLOWED_VIDEO_EXT = {".mp4", ".avi", ".mov", ".webm", ".mkv"}
MAX_VIDEO_SIZE_MB = 100


@app.post("/test/upload-video")
async def test_upload_video(file: UploadFile = File(..., description="Video file (MP4, AVI, MOV, WebM)")) -> dict[str, Any]:
    """
    Upload a video file to use as face source instead of live camera.
    Format: MP4, AVI, MOV, WebM, MKV. Max ~100MB.
    PerceptionAgent will read frames from this video (loops when done).
    """
    from cameras.camera_manager import set_video_face_source
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_VIDEO_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Use: {', '.join(ALLOWED_VIDEO_EXT)}",
        )
    content = await file.read()
    if len(content) > MAX_VIDEO_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large. Max {MAX_VIDEO_SIZE_MB}MB.")
    tmp = tempfile.mkdtemp(prefix="engageiq_video_")
    path = Path(tmp) / (file.filename or "video")
    path.write_bytes(content)
    set_video_face_source(str(path))
    return {"ok": True, "path": str(path), "format": ext}


@app.post("/test/clear-video")
def test_clear_video() -> dict[str, str]:
    """Switch back to live camera for face source."""
    from cameras.camera_manager import set_video_face_source
    set_video_face_source(None)
    return {"ok": True, "message": "Face: switched back to camera"}


@app.post("/test/upload-video-cam2")
async def test_upload_video_cam2(file: UploadFile = File(..., description="Video file for landing/takeoff")) -> dict[str, Any]:
    """Upload video for Camera 2 (external/landing/takeoff). LandingAgent uses this."""
    from cameras.camera_manager import set_video_external_source
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_VIDEO_EXT:
        raise HTTPException(status_code=400, detail=f"Unsupported format. Use: {', '.join(ALLOWED_VIDEO_EXT)}")
    content = await file.read()
    if len(content) > MAX_VIDEO_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large. Max {MAX_VIDEO_SIZE_MB}MB.")
    tmp = tempfile.mkdtemp(prefix="engageiq_cam2_")
    path = Path(tmp) / (file.filename or "video_cam2")
    path.write_bytes(content)
    set_video_external_source(str(path))
    return {"ok": True, "path": str(path), "format": ext}


@app.post("/test/clear-video-cam2")
def test_clear_video_cam2() -> dict[str, str]:
    """Switch back to live camera for external/landing source."""
    from cameras.camera_manager import set_video_external_source
    set_video_external_source(None)
    return {"ok": True, "message": "Cam2: switched back to camera"}


def update_phase(phase: str) -> None:
    """Called by sim_bridge to update flight phase."""
    _current_state["phase"] = phase


def update_signals(signals: dict[str, Any]) -> None:
    """Update rolling-window signals (yawn_count_10m, etc.)."""
    _current_state["signals"] = {**_current_state.get("signals", {}), **signals}


def append_cockpit_errors(errors: list[dict[str, Any]]) -> None:
    """Append cockpit errors from error_classifier."""
    _current_state.setdefault("cockpit_errors", []).extend(errors)


def set_landing_report(report: dict[str, Any]) -> None:
    """Set last landing report from LandingAgent."""
    _current_state["landing"] = report


# Export for cockpit/sim_bridge
def get_current_state() -> dict[str, Any]:
    return _current_state
