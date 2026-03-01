import React, { useCallback, useState } from 'react';

const SCENARIOS = [
  { id: 'nominal', label: 'Nominal', desc: 'PSI ~95+, green' },
  { id: 'drowsy', label: 'Drowsy', desc: 'WARNING, agent actions' },
  { id: 'critical', label: 'Critical', desc: 'Red, notify copilot' },
  { id: 'landing_bounce', label: 'Landing bounce', desc: 'Score 10, 4 bounces' },
  { id: 'cockpit_errors', label: 'Cockpit errors', desc: 'Procedural deductions' },
] as const;

// Hit backend directly to avoid proxy 404. Override with VITE_API_URL if backend is elsewhere.
function getTestInjectUrl(scenario: string): string {
  if (typeof window === 'undefined') return `http://localhost:8000/test/inject?scenario=${encodeURIComponent(scenario)}`;
  const base = (import.meta as any).env?.VITE_API_URL;
  const origin = base ? base.replace(/\/$/, '') : 'http://localhost:8000';
  return `${origin}/test/inject?scenario=${encodeURIComponent(scenario)}`;
}

export const SimulatorPanel: React.FC = () => {
  const [visible, setVisible] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const inject = useCallback(async (scenario: string) => {
    setLoading(scenario);
    setError(null);
    try {
      const r = await fetch(getTestInjectUrl(scenario), {
        method: 'POST',
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) {
        const detail = data?.detail ?? data?.error;
        const msg = Array.isArray(detail) ? detail.map((x: any) => x.msg || x).join(', ') : detail || `HTTP ${r.status}`;
        setError(r.status === 404 ? 'Backend route not found. Run backend from engageiq-flight/backend with: uvicorn main:app --port 8000' : msg);
        return;
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Request failed';
      setError(msg.includes('fetch') || msg.includes('Failed') ? 'Cannot reach backend. Is it running on http://localhost:8000?' : msg);
    } finally {
      setLoading(null);
    }
  }, []);

  return (
    <>
      {/* Toggle tab when panel is hidden */}
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        className="fixed top-20 right-0 z-50 px-3 py-2 rounded-l-lg bg-slate-800 border border-r-0 border-white/20 text-xs font-mono text-gray-300 hover:bg-slate-700 hover:text-white shadow-lg transition-colors"
        title={visible ? 'Hide simulator' : 'Show simulator'}
      >
        {visible ? '▶ Hide' : '◀ Simulator'}
      </button>

      {visible && (
        <div className="fixed top-20 right-0 z-40 w-72 bg-slate-900/98 border border-white/20 rounded-l-lg shadow-xl font-mono text-sm">
          <div className="flex items-center justify-between p-2 border-b border-white/10">
            <span className="text-hud-cyan font-semibold">Scenario simulator</span>
            <button
              type="button"
              onClick={() => setVisible(false)}
              className="text-gray-400 hover:text-white p-1 rounded"
              aria-label="Close"
            >
              ×
            </button>
          </div>
          <div className="p-3 space-y-2">
            {error && (
              <div className="text-hud-red text-xs bg-red-900/30 rounded p-2">
                {error}
              </div>
            )}
            {SCENARIOS.map(({ id, label, desc }) => (
              <button
                key={id}
                type="button"
                disabled={loading !== null}
                onClick={() => inject(id)}
                className="w-full text-left px-3 py-2 rounded bg-slate-800 hover:bg-slate-700 border border-white/10 disabled:opacity-50 transition-colors"
              >
                <span className="text-white">{label}</span>
                <span className="block text-xs text-gray-400 mt-0.5">{desc}</span>
                {loading === id && <span className="text-hud-cyan text-xs"> …</span>}
              </button>
            ))}
          </div>
        </div>
      )}
    </>
  );
};
