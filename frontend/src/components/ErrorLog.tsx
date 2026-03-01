import React from 'react';
import type { CockpitError } from '../types/feed';

interface ErrorLogProps {
  errors: CockpitError[];
  maxItems?: number;
}

export const ErrorLog: React.FC<ErrorLogProps> = ({ errors, maxItems = 8 }) => {
  const list = errors.slice(-maxItems).reverse();
  return (
    <div className="bg-hud-panel rounded-lg p-4 border border-white/10">
      <div className="font-display text-sm uppercase text-gray-400 tracking-wider mb-2">
        Cockpit errors
      </div>
      <ul className="font-mono text-xs space-y-1 max-h-28 overflow-y-auto">
        {list.length === 0 ? (
          <li className="text-gray-500">No errors</li>
        ) : (
          list.map((e, i) => (
            <li key={i} className="text-hud-orange">
              <span className="text-gray-500">[{e.type}]</span> {e.description}
              {e.points_deducted != null && (
                <span className="text-gray-400 ml-1">(-{e.points_deducted})</span>
              )}
            </li>
          ))
        )}
      </ul>
    </div>
  );
};
