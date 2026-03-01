"""
PerceptionAgent — Gemma 3n E4B face analysis.
Input: raw face frame (Camera A) + flight phase.
Output: pilot_state JSON (state, perclos_est, yawn, head_drop, gaze_off_instruments, etc.)
Runs every 2 seconds.
"""
from __future__ import annotations

import base64
import json
import re
from typing import Any

import httpx

from config import config


# Default when no image / Ollama unavailable
DEFAULT_STATE = {
    "state": "ALERT",
    "perclos_est": 0.0,
    "yawn": False,
    "head_drop": False,
    "gaze_off_instruments": False,
    "confidence": 0.0,
    "reason": "No frame or model unavailable",
}


class PerceptionAgent:
    """Calls Ollama Gemma 3n with face image + prompt, parses JSON pilot_state."""

    def __init__(self, model: str | None = None, host: str | None = None) -> None:
        self.model = model or config.ollama_perception_model
        self.host = (host or config.ollama_host).rstrip("/")
        self._last_frame_b64: str | None = None

    def set_frame(self, jpeg_bytes: bytes) -> None:
        """Set current frame for next run_once (base64)."""
        self._last_frame_b64 = base64.b64encode(jpeg_bytes).decode("ascii")

    async def run_once(self, phase: str = "cruise", frame_b64: str | None = None) -> dict[str, Any] | None:
        """
        Run one perception step. If frame not provided, use last set frame or return default.
        """
        b64 = frame_b64 or self._last_frame_b64
        prompt = (
            "You are a pilot fatigue detection system. Flight phase: " + phase + ". "
            "Analyze this pilot's face frame for: drowsiness, yawning, head pose deviation, gaze direction. "
            "Return JSON only, no markdown:\n"
            '{"state": "ALERT|FATIGUED|DROWSY|CRITICAL", "perclos_est": 0-100, "yawn": bool, '
            '"head_drop": bool, "gaze_off_instruments": bool, "confidence": 0-1, "reason": "string"}\n'
        )
        if not b64:
            return DEFAULT_STATE

        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        # Ollama vision API: images array of base64 data
        payload["images"] = [b64]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(f"{self.host}/api/generate", json=payload)
                r.raise_for_status()
                data = r.json()
                text = (data.get("response") or "").strip()
        except Exception:
            return DEFAULT_STATE

        return self._parse_response(text) or DEFAULT_STATE

    def _parse_response(self, text: str) -> dict[str, Any] | None:
        """Extract JSON object from model output."""
        # Try raw JSON block
        match = re.search(r"\{[^{}]*\"state\"[^{}]*\}", text, re.DOTALL)
        if not match:
            match = re.search(r"\{[\s\S]*?\}", text)
        if not match:
            return None
        try:
            obj = json.loads(match.group())
            # Normalize types
            state = obj.get("state", "ALERT")
            if state not in ("ALERT", "FATIGUED", "DROWSY", "CRITICAL"):
                state = "ALERT"
            return {
                "state": state,
                "perclos_est": float(obj.get("perclos_est", 0) or 0),
                "yawn": bool(obj.get("yawn", False)),
                "head_drop": bool(obj.get("head_drop", False)),
                "gaze_off_instruments": bool(obj.get("gaze_off_instruments", False)),
                "confidence": float(obj.get("confidence", 0) or 0),
                "reason": str(obj.get("reason", "") or ""),
            }
        except (json.JSONDecodeError, TypeError):
            return None
