#!/usr/bin/env python3
"""
Capture real UI screenshots of each scenario.
Requires: backend (port 8000) and frontend (port 5173) running.

Run:
  pip install playwright httpx
  playwright install chromium

  # In one terminal: cd backend && uvicorn main:app --port 8000
  # In another:     cd frontend && npm run dev

  python scripts/capture_scenario_screenshots.py

Output: slides/screenshots/warning_ui.png, critical_ui.png, landing_ui.png, cockpit_ui.png, nominal_ui.png
"""
from __future__ import annotations

import asyncio
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Install: pip install playwright && playwright install chromium")
    raise

try:
    import httpx
except ImportError:
    print("Install: pip install httpx")
    raise

API_BASE = "http://localhost:8000"
APP_URL = "http://localhost:5173"
SCREENSHOTS_DIR = Path(__file__).parent.parent / "slides" / "screenshots"
SCENARIOS = [
    ("nominal", "nominal"),
    ("warning", "drowsy"),
    ("critical", "critical"),
    ("landing", "landing_bounce"),
    ("cockpit", "cockpit_errors"),
]


async def inject_scenario(name: str) -> bool:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(f"{API_BASE}/test/inject?scenario={name}")
        return r.status_code == 200


async def capture_all() -> None:
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await context.new_page()

        try:
            await page.goto(APP_URL, wait_until="networkidle", timeout=15000)
        except Exception as e:
            print(f"Cannot load {APP_URL}. Is frontend running? (npm run dev)\n{e}")
            await browser.close()
            return

        for label, scenario in SCENARIOS:
            print(f"Injecting {scenario}...", end=" ")
            ok = await inject_scenario(scenario)
            if not ok:
                print("FAILED (backend down?)")
                continue
            await asyncio.sleep(1.2)  # Wait for WebSocket to update HUD
            path = SCREENSHOTS_DIR / f"{label}_ui.png"
            await page.screenshot(path=str(path))
            print(f"Saved {path.name}")

        await browser.close()
    print(f"\nDone. Screenshots in {SCREENSHOTS_DIR}")
    print("Run: python scripts/generate_presentation.py to rebuild PPT with images.")


if __name__ == "__main__":
    asyncio.run(capture_all())
