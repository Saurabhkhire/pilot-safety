import React, { useCallback, useEffect, useState } from 'react';

const SCENARIO_LABELS: Record<string, string> = {
  nominal: 'Nominal',
  fatigue_onset: 'Fatigue onset',
  drowsy: 'Drowsy',
  gaze_drift: 'Gaze drift',
  yawn_series: 'Yawn series',
  critical: 'Critical',
  micro_sleep: 'Micro-sleep',
  head_drop_severe: 'Head drop severe',
  takeoff_smooth: 'Takeoff smooth',
  approach_nominal: 'Approach nominal',
  landing_greaser: 'Landing greaser',
  landing_hard: 'Landing hard',
  landing_bounce: 'Landing bounce',
  go_around: 'Go-around',
  cockpit_sequence: 'Cockpit sequence',
  cockpit_errors: 'Cockpit errors',
  cockpit_gear_omission: 'Cockpit gear omission',
  cockpit_wrong_button: 'Cockpit wrong button',
  cockpit_reversal: 'Cockpit reversal',
  cockpit_multi: 'Cockpit multi',
};

function getApiBase(): string {
  if (typeof window === 'undefined') return 'http://localhost:8000';
  const base = (import.meta as any).env?.VITE_API_URL;
  return base ? base.replace(/\/$/, '') : 'http://localhost:8000';
}

const GROUPS: Record<string, string> = {
  nominal: 'nominal',
  fatigue_onset: 'warning', drowsy: 'warning', gaze_drift: 'warning', yawn_series: 'warning',
  critical: 'critical', micro_sleep: 'critical', head_drop_severe: 'critical',
  takeoff_smooth: 'takeoff_landing', approach_nominal: 'takeoff_landing', landing_greaser: 'takeoff_landing',
  landing_hard: 'takeoff_landing', landing_bounce: 'takeoff_landing', go_around: 'takeoff_landing',
  cockpit_sequence: 'cockpit', cockpit_errors: 'cockpit', cockpit_gear_omission: 'cockpit',
  cockpit_wrong_button: 'cockpit', cockpit_reversal: 'cockpit', cockpit_multi: 'cockpit',
};
const GROUP_LABELS: Record<string, string> = {
  nominal: 'Nominal',
  warning: 'Warning',
  critical: 'Critical',
  takeoff_landing: 'Takeoff / Landing',
  cockpit: 'Cockpit Errors',
  other: 'Other',
};

export const SimulatorPanel: React.FC = () => {
  const [visible, setVisible] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scenariosFromBackend, setScenariosFromBackend] = useState<string[]>([]);

  useEffect(() => {
    let cancelled = false;
    fetch(`${getApiBase()}/test/scenarios`)
      .then((r) => r.json())
      .then((data) => {
        if (!cancelled && Array.isArray(data?.scenarios)) setScenariosFromBackend(data.scenarios);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  const scenarios = scenariosFromBackend.length > 0
    ? scenariosFromBackend
    : ['nominal', 'drowsy', 'critical', 'landing_bounce', 'cockpit_errors'];

  const inject = useCallback(async (scenario: string) => {
    setLoading(scenario);
    setError(null);
    try {
      const r = await fetch(`${getApiBase()}/test/inject?scenario=${encodeURIComponent(scenario)}`, { method: 'POST' });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) {
        const detail = data?.detail ?? data?.error;
        const msg = Array.isArray(detail) ? detail.map((x: any) => x.msg || x).join(', ') : detail || `HTTP ${r.status}`;
        setError(r.status === 404 ? 'Backend route not found. Run: uvicorn main:app --port 8000' : msg);
        return;
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Request failed';
      setError(msg.includes('fetch') || msg.includes('Failed') ? 'Cannot reach backend on http://localhost:8000' : msg);
    } finally {
      setLoading(null);
    }
  }, []);

  const groups = Array.from(new Set(scenarios.map((id) => GROUPS[id] || 'other'))).filter(Boolean);
  return (
    <>
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        className="fixed top-36 right-0 z-50 px-3 py-2 rounded-l-lg bg-slate-800 border border-r-0 border-white/20 text-xs font-mono text-gray-300 hover:bg-slate-700 hover:text-white shadow-lg transition-colors"
        title={visible ? 'Hide simulator' : 'Show simulator'}
      >
        {visible ? '▶ Hide' : '◀ Simulator'}
      </button>

      {visible && (
        <div className="fixed top-36 right-0 z-40 w-80 max-h-[70vh] bg-slate-900/98 border border-white/20 rounded-l-lg shadow-xl font-mono text-sm flex flex-col">
          <div className="flex items-center justify-between p-2 border-b border-white/10 shrink-0">
            <span className="text-hud-cyan font-semibold">Scenario simulator</span>
            <button type="button" onClick={() => setVisible(false)} className="text-gray-400 hover:text-white p-1 rounded" aria-label="Close">×</button>
          </div>
          <div className="p-3 space-y-3 overflow-y-auto">
            {error && <div className="text-hud-red text-xs bg-red-900/30 rounded p-2 shrink-0">{error}</div>}

            {groups.map((group) => (
              <div key={group}>
                <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">{GROUP_LABELS[group] || group}</div>
                <div className="flex flex-wrap gap-1">
                  {scenarios.filter((id) => (GROUPS[id] || 'other') === group).map((id) => (
                    <button
                      key={id}
                      type="button"
                      disabled={loading !== null}
                      onClick={() => inject(id)}
                      className="px-2 py-1.5 rounded bg-slate-800 hover:bg-slate-700 border border-white/10 text-xs disabled:opacity-50 truncate max-w-full"
                    >
                      {loading === id ? '…' : SCENARIO_LABELS[id] || id}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
};
