"""
Simulator bridge — X-Plane xpc or pre-recorded flight data JSON replay.
Detects flight phase, button events, landing contact events.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Callable, Optional

from config import config

# Phase callback: (phase: str) -> None
_phase_callback: Optional[Callable[[str], None]] = None
# Error callback: (errors: list[dict]) -> None
_error_callback: Optional[Callable[[list], None]] = None

_replay_data: list[dict[str, Any]] = []
_replay_index = 0


def set_phase_callback(cb: Callable[[str], None]) -> None:
    global _phase_callback
    _phase_callback = cb


def set_error_callback(cb: Callable[[list], None]) -> None:
    global _error_callback
    _error_callback = cb


def load_replay(path: str | Path) -> bool:
    """Load pre-recorded flight events JSON (list of {ts, phase?, event?, ...})."""
    global _replay_data, _replay_index
    p = Path(path)
    if not p.exists():
        return False
    try:
        raw = p.read_text()
        _replay_data = json.loads(raw) if raw.strip() else []
        _replay_index = 0
        return True
    except Exception:
        return False


def get_phase_from_replay(now_ts: float) -> str:
    """Return phase for given timestamp from replay; default cruise."""
    global _replay_index
    phase = "cruise"
    for i, ev in enumerate(_replay_data):
        if ev.get("ts", 0) <= now_ts:
            if "phase" in ev:
                phase = ev["phase"]
            _replay_index = i
        else:
            break
    return phase


async def run_replay_loop() -> None:
    """
    If REPLAY_JSON is set, advance replay and invoke phase/error callbacks.
    Otherwise do nothing (X-Plane would be used in production).
    """
    path = config.replay_json_path
    if not path or not load_replay(path):
        return
    import time
    t0 = time.time()
    while True:
        now = time.time() - t0
        phase = get_phase_from_replay(now)
        if _phase_callback:
            _phase_callback(phase)
        # Emit errors from replay events
        for ev in _replay_data:
            if ev.get("ts", 0) <= now and ev.get("event") == "cockpit_error" and _error_callback:
                _error_callback(ev.get("errors", []))
        await asyncio.sleep(0.5)


# X-Plane xpc placeholder — real impl would connect to X-Plane plugin
def connect_xplane() -> bool:
    """Return True if X-Plane connection available."""
    return False
