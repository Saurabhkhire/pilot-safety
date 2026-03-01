"""
Flight phase detection from sim data or replay.
Phases: pre_takeoff, takeoff, climb, cruise, approach, landing, taxi.
"""
from __future__ import annotations

from typing import Any


def phase_from_sim_data(data: dict[str, Any]) -> str:
    """
    Derive phase from X-Plane-style data (altitude_ft, vsi, gear, etc.).
    Fallback: cruise.
    """
    alt = float(data.get("altitude_ft", 0) or 0)
    vsi = float(data.get("vsi_fpm", 0) or 0)
    gear = data.get("gear_down", False)
    gs = float(data.get("ground_speed_kt", 0) or 0)

    if alt < 50 and gs < 30:
        return "taxi" if gs > 5 else "pre_takeoff"
    if alt < 500 and vsi > 200:
        return "takeoff"
    if alt < 10000 and vsi > 100:
        return "climb"
    if gear and alt < 2000 and vsi < -100:
        return "approach"
    if gear and alt < 100:
        return "landing"
    return "cruise"
