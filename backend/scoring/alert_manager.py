"""
Alert manager — PSI threshold → alert level and copy for HUD.
"""
from __future__ import annotations

from typing import Any

# 85-100 → NOMINAL, 70-84 → MONITOR, 55-69 → CAUTION, 35-54 → WARNING, 0-34 → CRITICAL
_LEVELS = [
    (85, "nominal", "NOMINAL", "green", "All systems nominal."),
    (70, "monitor", "MONITOR", "cyan", "Increase monitoring. Poll rate elevated."),
    (55, "caution", "CAUTION", "yellow", "Audio chime. Monitor pilot attentiveness."),
    (35, "warning", "WARNING", "orange", "Verbal alert recommended. Consider rest protocol."),
    (0, "critical", "CRITICAL", "red", "Co-pilot notification. ATC advisory possible."),
]


def get_alert_for_psi(psi: float) -> dict[str, Any]:
    """Return alert level, title, color, and sub message for given PSI."""
    for threshold, level, title, color, sub in _LEVELS:
        if psi >= threshold:
            return {
                "level": level,
                "title": title,
                "color": color,
                "sub": sub,
            }
    t = _LEVELS[-1]
    return {"level": t[1], "title": t[2], "color": t[3], "sub": t[4]}
