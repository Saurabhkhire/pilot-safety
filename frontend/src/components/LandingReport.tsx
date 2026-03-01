import React from 'react';
import type { LandingReport as LandingReportType } from '../types/feed';

interface LandingReportProps {
  landing: LandingReportType | null;
}

export const LandingReport: React.FC<LandingReportProps> = ({ landing }) => {
  if (!landing) {
    return (
      <div className="bg-hud-panel rounded-lg p-4 border border-white/10 font-mono text-sm text-gray-500">
        No landing data
      </div>
    );
  }
  const score = landing.score ?? 0;
  const color = score >= 80 ? 'text-hud-green' : score >= 50 ? 'text-hud-yellow' : 'text-hud-red';
  return (
    <div className="bg-hud-panel rounded-lg p-4 border border-white/10">
      <div className="font-display text-sm uppercase text-gray-400 tracking-wider mb-2">Landing Report</div>
      <div className="flex items-center gap-4 flex-wrap">
        <span className={`text-2xl font-bold ${color}`}>{score}</span>
        <span className="text-gray-400">/ 100</span>
        {landing.contact_type && (
          <span className="text-white capitalize">{landing.contact_type}</span>
        )}
        {landing.bounce_count != null && landing.bounce_count > 0 && (
          <span className="text-hud-orange">Bounces: {landing.bounce_count}</span>
        )}
        {landing.on_centerline === false && (
          <span className="text-hud-yellow">Off centerline</span>
        )}
      </div>
      {landing.events && landing.events.length > 0 && (
        <div className="mt-2 flex gap-1 flex-wrap">
          {landing.events.map((ev, i) => (
            <span
              key={i}
              className="px-2 py-0.5 rounded bg-white/10 text-xs text-gray-300"
            >
              {ev.type} @{ev.t_ms}ms
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
