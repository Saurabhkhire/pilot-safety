"""
Landing report card — score from LandingAgent JSON (bounce_count, contact_type, centerline).
"""
from __future__ import annotations

from typing import Any


def score_landing(report: dict[str, Any]) -> int:
    """
    Compute 0–100 landing score from LandingAgent output.
    - 1 contact, greaser → 100
    - 1 contact, firm → 80, hard → 60
    - 2 contacts → 50, 3 → 30, 4+ → 10
    - Centerline deviation >5ft → -10, long landing → -15
    """
    bounce_count = int(report.get("bounce_count", 0) or 0)
    contact_type = (report.get("contact_type") or "firm").lower()
    on_centerline = report.get("on_centerline", True)
    long_landing = report.get("long_landing", False)

    if bounce_count >= 4:
        base = 10
    elif bounce_count == 3:
        base = 30
    elif bounce_count == 2:
        base = 50
    else:
        if contact_type == "greaser":
            base = 100
        elif contact_type == "firm":
            base = 80
        elif contact_type == "hard":
            base = 60
        else:
            base = 60

    if not on_centerline:
        base -= 10
    if long_landing:
        base -= 15
    return max(0, min(100, base))
