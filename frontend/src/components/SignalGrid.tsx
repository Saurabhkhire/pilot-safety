import React from 'react';
import type { Signals, PilotState } from '../types/feed';

interface SignalGridProps {
  signals: Signals;
  pilot_state: PilotState | null;
}

const CARDS = [
  { key: 'yawn_count_10m', label: 'Yawns (10m)', unit: '' },
  { key: 'head_drop_count_30m', label: 'Head drops (30m)', unit: '' },
  { key: 'gaze_off_pct', label: 'Gaze off %', unit: '%' },
  { key: 'critical_events_1h', label: 'Critical (1h)', unit: '' },
];

export const SignalGrid: React.FC<SignalGridProps> = ({ signals, pilot_state }) => {
  return (
    <div className="grid grid-cols-2 gap-2">
      {CARDS.map(({ key, label, unit }) => (
        <div
          key={key}
          className="bg-hud-panel rounded-lg p-3 border border-white/10 font-mono text-sm"
        >
          <div className="text-gray-400 text-xs uppercase tracking-wider">{label}</div>
          <div className="text-hud-cyan text-lg">
            {signals[key as keyof Signals] ?? 0}
            {unit}
          </div>
        </div>
      ))}
      {pilot_state && (
        <div className="col-span-2 bg-hud-panel rounded-lg p-3 border border-white/10 font-mono text-xs text-gray-300">
          State: <span className="text-white">{pilot_state.state}</span> — {pilot_state.reason || '—'}
        </div>
      )}
    </div>
  );
};
