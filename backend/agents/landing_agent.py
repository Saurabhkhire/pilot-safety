"""
LandingAgent — Gemma 3n E4B landing frame analysis (Camera B).
Only active when phase = approach or landing.
Output: landing_report JSON (bounce_count, on_centerline, contact_type, score).
"""
from __future__ import annotations

import base64
import json
import re
from typing import Any

import httpx

from config import config
from scoring.landing_scorer import score_landing


class LandingAgent:
    """Calls Ollama Gemma 3n with external/belly cam frame, parses landing JSON."""

    def __init__(self, model: str | None = None, host: str | None = None) -> None:
        self.model = model or config.ollama_landing_model
        self.host = (host or config.ollama_host).rstrip("/")

    async def run_once(self, frame_b64: str, phase: str = "landing") -> dict[str, Any] | None:
        """
        Analyze one landing frame. Returns report with bounce_count, on_centerline, contact_type, score.
        """
        prompt = (
            "Analyze this aircraft landing frame. Count vertical bounce events. "
            "Is the aircraft on centerline? Estimate touchdown quality. "
            "Return JSON only, no markdown:\n"
            '{"bounce_count": int, "on_centerline": bool, "contact_type": "greaser|firm|hard|bounce", '
            '"score": 0-100, "long_landing": bool}\n'
        )
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "images": [frame_b64],
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.post(f"{self.host}/api/generate", json=payload)
                r.raise_for_status()
                data = r.json()
                text = (data.get("response") or "").strip()
        except Exception:
            return None

        report = self._parse_response(text)
        if report is not None:
            report["score"] = score_landing(report)
            report["events"] = report.get("events") or []
        return report

    def _parse_response(self, text: str) -> dict[str, Any] | None:
        match = re.search(r"\{[\s\S]*?\}", text)
        if not match:
            return None
        try:
            obj = json.loads(match.group())
            bounce_count = int(obj.get("bounce_count", 0) or 0)
            contact_type = (obj.get("contact_type") or "firm").lower()
            if contact_type not in ("greaser", "firm", "hard", "bounce"):
                contact_type = "firm"
            return {
                "bounce_count": bounce_count,
                "on_centerline": bool(obj.get("on_centerline", True)),
                "contact_type": contact_type,
                "long_landing": bool(obj.get("long_landing", False)),
                "events": obj.get("events", []),
            }
        except (json.JSONDecodeError, TypeError):
            return None
