"""
PSI Scoring Engine — composite Pilot Safety Index from perception + cockpit + landing.
Inputs: rolling window of PerceptionAgent outputs + ActionAgent events.
"""
from __future__ import annotations


def compute_psi(window: dict) -> float:
    """
    Compute Pilot Safety Index 0–100 from rolling window.
    """
    score = 100.0

    # FATIGUE COMPONENT (max -40pts) — from Gemma perclos_est
    perclos = float(window.get("perclos_est", 0) or 0)
    if perclos > 25:
        score -= 40
    elif perclos > 15:
        score -= 25
    elif perclos > 8:
        score -= 12

    # Yawn frequency (from Gemma yawn bool over 10min window)
    yawns_per_10m = int(window.get("yawn_count_10m", 0) or 0)
    if yawns_per_10m >= 4:
        score -= 15
    elif yawns_per_10m >= 2:
        score -= 7

    # Micro-sleep: any CRITICAL state from Gemma = -15 per event
    critical_events = int(window.get("critical_events_1h", 0) or 0)
    score -= min(30, critical_events * 15)

    # ATTENTION COMPONENT (max -30pts)
    head_drop = int(window.get("head_drop_count_30m", 0) or 0)
    if head_drop > 3:
        score -= 20
    elif head_drop > 1:
        score -= 10

    gaze_off_pct = float(window.get("gaze_off_pct", 0) or 0)
    if gaze_off_pct > 20:
        score -= 15
    elif gaze_off_pct > 10:
        score -= 7

    # PROCEDURAL COMPONENT (max -30pts) — from cockpit error events
    cockpit_points = int(window.get("cockpit_error_points_session", 0) or 0)
    score -= min(30, cockpit_points)

    # LANDING PENALTY — if last landing scored <40, apply -10
    last_landing = window.get("last_landing_score", 100)
    if last_landing is not None and last_landing < 40:
        score -= 10

    return max(0.0, min(100.0, round(score, 1)))
