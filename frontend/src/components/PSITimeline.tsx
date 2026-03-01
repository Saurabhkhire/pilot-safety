import React, { useEffect, useRef, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';

interface PSITimelineProps {
  currentPsi: number;
  maxPoints?: number;
}

export const PSITimeline: React.FC<PSITimelineProps> = ({ currentPsi, maxPoints = 60 }) => {
  const [data, setData] = useState<Array<{ t: number; psi: number }>>([]);
  const t0 = useRef(Date.now() / 1000);

  useEffect(() => {
    const t = Date.now() / 1000 - t0.current;
    setData((prev) => {
      const next = [...prev, { t, psi: currentPsi }];
      return next.length > maxPoints ? next.slice(-maxPoints) : next;
    });
  }, [currentPsi, maxPoints]);

  if (data.length < 2) {
    return (
      <div className="bg-hud-panel rounded-lg p-4 border border-white/10 h-32 flex items-center justify-center text-gray-500 font-mono text-sm">
        PSI timeline…
      </div>
    );
  }

  return (
    <div className="bg-hud-panel rounded-lg p-4 border border-white/10 h-32">
      <div className="font-display text-xs uppercase text-gray-400 tracking-wider mb-1">PSI (live)</div>
      <ResponsiveContainer width="100%" height="80%">
        <LineChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <XAxis dataKey="t" hide />
          <YAxis domain={[0, 100]} hide />
          <Tooltip
            formatter={(v: number) => [v.toFixed(1), 'PSI']}
            contentStyle={{ background: 'rgba(0,20,40,0.9)', border: '1px solid rgba(255,255,255,0.2)' }}
            labelFormatter={(t) => `t = ${Number(t).toFixed(1)}s`}
          />
          <Line
            type="monotone"
            dataKey="psi"
            stroke="#00d4ff"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
