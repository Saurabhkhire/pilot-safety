"""
Cockpit error classification — 5 types with point deductions.
Per-phase expected action model loaded from JSON per aircraft type.
"""
from __future__ import annotations

from typing import Any

# Error types: wrong_button, omission, commission, reversal, sequence_error
# Severity 1/2/3 and points_deducted per spec
ERROR_CONFIG = {
    "wrong_button": {"points": 20, "severity": 3},
    "omission": {"points": 8, "severity": 2},
    "commission": {"points": 8, "severity": 2},
    "reversal": {"points": 20, "severity": 3},
    "sequence_error": {"points": 2, "severity": 1},
}


def classify(
    error_type: str,
    description: str,
    ts: float,
) -> dict[str, Any]:
    """
    Return event dict for PSI engine: ts, type, description, severity, points_deducted.
    """
    cfg = ERROR_CONFIG.get(error_type, {"points": 5, "severity": 2})
    return {
        "ts": ts,
        "type": error_type,
        "description": description,
        "severity": cfg["severity"],
        "points_deducted": cfg["points"],
    }


def from_sim_event(sim_event: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Convert raw sim event (e.g. from replay or xpc) to list of classified errors.
    """
    out: list[dict[str, Any]] = []
    t = float(sim_event.get("ts", 0))
    etype = sim_event.get("type") or sim_event.get("error_type") or "omission"
    desc = sim_event.get("description") or sim_event.get("message") or "Cockpit procedural error"
    out.append(classify(etype, desc, t))
    return out
