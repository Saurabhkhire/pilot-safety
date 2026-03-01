# Screenshots for the presentation

## Option 1: Auto-capture (recommended)

With **backend** and **frontend** running:

```bash
pip install playwright httpx
playwright install chromium

# Terminal 1: cd backend && uvicorn main:app --port 8000
# Terminal 2: cd frontend && npm run dev
# Terminal 3:
python scripts/capture_scenario_screenshots.py
```

This injects each scenario, waits for the HUD to update, and saves real screenshots:
- `nominal_ui.png`, `warning_ui.png`, `critical_ui.png`, `landing_ui.png`, `cockpit_ui.png`

## Option 2: Upload scenario images (filename = scenario)

In the **Simulator** panel, use "Upload image (drowsy.png, critical.jpg, etc.)":

- Upload `drowsy.png` or `warning.jpg` → injects **drowsy** (WARNING) simulation, HUD updates
- Upload `critical.png` or `critical.jpg` → injects **critical** (CRITICAL) simulation
- Upload `landing.png` or `landing_bounce.jpg` → injects **landing_bounce** simulation
- Upload `cockpit.png` or `cockpit_errors.jpg` → injects **cockpit_errors** simulation
- Upload `nominal.png` → injects **nominal** (green) simulation

Images are saved to this folder for use in the PPT. Filename (before extension) determines the scenario. Formats: PNG, JPEG/JPG, WebP.

## Option 3: Manual screenshots

1. Open http://localhost:5173
2. Open Simulator → inject each scenario (nominal, drowsy, critical, landing_bounce, cockpit_errors)
3. Screenshot each state (Win+Shift+S, Snipping Tool, etc.)
4. Save as `warning_ui.png`, `critical_ui.png`, etc. in this folder

## Rebuild PPT with images

```bash
python scripts/generate_presentation.py
```
