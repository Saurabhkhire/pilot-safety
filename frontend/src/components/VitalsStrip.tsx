import React from 'react';
import type { PSIFeed } from '../types/feed';

interface VitalsStripProps {
  data: PSIFeed | null;
}

export const VitalsStrip: React.FC<VitalsStripProps> = ({ data }) => {
  if (!data) {
    return (
      <div className="flex items-center gap-4 px-4 py-2 bg-hud-panel rounded font-mono text-sm text-gray-500">
        Waiting for feed…
      </div>
    );
  }
  const ps = data.pilot_state;
  return (
    <div className="flex items-center gap-6 px-4 py-2 bg-hud-panel rounded font-mono text-sm flex-wrap">
      <span className="text-gray-400">PSI</span>
      <span className="text-white font-semibold">{data.psi.toFixed(1)}</span>
      <span className="text-gray-500">|</span>
      <span className="text-gray-400">Phase</span>
      <span className="text-hud-cyan uppercase">{data.phase}</span>
      {ps && (
        <>
          <span className="text-gray-500">|</span>
          <span className="text-gray-400">State</span>
          <span className="text-white">{ps.state}</span>
          <span className="text-gray-400">Perclos</span>
          <span className="text-white">{ps.perclos_est?.toFixed(1) ?? 0}%</span>
        </>
      )}
    </div>
  );
};
