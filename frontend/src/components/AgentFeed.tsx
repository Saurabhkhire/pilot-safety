import React from 'react';

interface AgentFeedProps {
  actions: string[];
}

export const AgentFeed: React.FC<AgentFeedProps> = ({ actions }) => {
  return (
    <div className="bg-hud-panel rounded-lg p-4 border border-white/10">
      <div className="font-display text-sm uppercase text-gray-400 tracking-wider mb-2">
        Agent actions (FunctionGemma)
      </div>
      <ul className="font-mono text-xs space-y-1 max-h-32 overflow-y-auto">
        {actions.length === 0 ? (
          <li className="text-gray-500">No actions</li>
        ) : (
          actions.map((a, i) => (
            <li key={i} className="text-hud-cyan truncate" title={a}>
              {a}
            </li>
          ))
        )}
      </ul>
    </div>
  );
};
