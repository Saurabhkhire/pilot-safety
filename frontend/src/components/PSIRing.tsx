import React from 'react';

interface PSIRingProps {
  psi: number;
  size?: number;
  strokeWidth?: number;
}

const LEVEL_COLORS: Record<string, string> = {
  nominal: '#00ff88',
  monitor: '#00d4ff',
  caution: '#ffcc00',
  warning: '#ff8800',
  critical: '#ff3366',
};

function levelForPsi(psi: number): string {
  if (psi >= 85) return 'nominal';
  if (psi >= 70) return 'monitor';
  if (psi >= 55) return 'caution';
  if (psi >= 35) return 'warning';
  return 'critical';
}

export const PSIRing: React.FC<PSIRingProps> = ({ psi, size = 200, strokeWidth = 14 }) => {
  const level = levelForPsi(psi);
  const color = LEVEL_COLORS[level] ?? LEVEL_COLORS.nominal;
  const r = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * r;
  const dash = (psi / 100) * circumference;

  return (
    <div className="flex flex-col items-center font-display">
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={circumference - dash}
          strokeLinecap="round"
          className="transition-all duration-500"
        />
      </svg>
      <span className="text-4xl font-bold mt-2" style={{ color }}>
        {Math.round(psi)}
      </span>
      <span className="text-sm uppercase tracking-wider text-gray-400">PSI</span>
    </div>
  );
};
