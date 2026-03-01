"""
ActionAgent — FunctionGemma 270M fine-tuned agentic function caller.
Input: pilot_state stream + session context.
Output: list of function call strings (trigger_alert, notify_copilot, suggest_rest_protocol, etc.)
"""
from __future__ import annotations

import json
import re
from typing import Any

import httpx

from config import config

# Functions the agent can call (for parsing)
FUNCTIONS = [
    "trigger_alert",
    "notify_copilot",
    "suggest_rest_protocol",
    "log_fatigue_event",
    "request_atc_advisory",
    "adjust_psi_score",
]


class ActionAgent:
    """Calls Ollama FunctionGemma with pilot_state, parses function call lines."""

    def __init__(self, model: str | None = None, host: str | None = None) -> None:
        self.model = model or config.ollama_action_model
        self.host = (host or config.ollama_host).rstrip("/")

    async def run_once(
        self,
        pilot_state: dict[str, Any],
        phase: str = "cruise",
        context: dict[str, Any] | None = None,
    ) -> list[str]:
        """
        Send pilot_state to action model; return list of function call strings
        e.g. ['trigger_alert(WARNING, "Drowsiness detected")', 'suggest_rest_protocol(15)']
        """
        ctx = context or {}
        state_str = json.dumps(pilot_state, indent=0)
        prompt = (
            "You are a pilot safety action agent. Given this pilot state and phase, "
            "output only the function calls to perform, one per line. No explanation.\n"
            f"Phase: {phase}\n"
            f"Pilot state:\n{state_str}\n"
            "Available functions: trigger_alert(level, message), notify_copilot(reason), "
            "suggest_rest_protocol(duration_min), log_fatigue_event(type, severity), "
            "request_atc_advisory(reason), adjust_psi_score(delta, reason).\n"
            "Output function calls only:"
        )
        payload = {"model": self.model, "prompt": prompt, "stream": False}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(f"{self.host}/api/generate", json=payload)
                r.raise_for_status()
                data = r.json()
                text = (data.get("response") or "").strip()
        except Exception:
            return self._fallback_actions(pilot_state, phase)

        return self._parse_calls(text) or self._fallback_actions(pilot_state, phase)

    def _parse_calls(self, text: str) -> list[str]:
        """Extract function call lines from model output."""
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        out: list[str] = []
        for ln in lines:
            for fn in FUNCTIONS:
                if fn in ln and "(" in ln:
                    # Take first parenthesized call per line
                    start = ln.find(fn)
                    if start >= 0:
                        rest = ln[start:]
                        depth = 0
                        end = -1
                        for i, c in enumerate(rest):
                            if c == "(":
                                depth += 1
                            elif c == ")":
                                depth -= 1
                                if depth == 0:
                                    end = i + 1
                                    break
                        if end > 0:
                            out.append(rest[:end])
                    break
        return out

    def _fallback_actions(self, pilot_state: dict[str, Any], phase: str) -> list[str]:
        """Rule-based fallback when model unavailable or returns nothing."""
        state = pilot_state.get("state", "ALERT")
        perclos = float(pilot_state.get("perclos_est", 0) or 0)
        actions: list[str] = []
        if state == "CRITICAL" or perclos > 25:
            actions.append('trigger_alert(CRITICAL, "Pilot fatigue critical")')
            actions.append("notify_copilot(reason='Critical fatigue state')")
        elif state == "DROWSY" or perclos > 15:
            actions.append('trigger_alert(WARNING, "Drowsiness detected")')
            actions.append("suggest_rest_protocol(15)")
        elif state == "FATIGUED" or perclos > 8:
            actions.append("log_fatigue_event(perclos_elevated, severity=2)")
        return actions
