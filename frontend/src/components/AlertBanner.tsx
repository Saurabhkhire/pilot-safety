import React from 'react';
import type { Alert } from '../types/feed';

interface AlertBannerProps {
  alert: Alert | null;
  onDismiss?: () => void;
  flash?: boolean;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({ alert, onDismiss, flash = false }) => {
  if (!alert) return null;
  const isCritical = alert.level === 'critical';
  const borderColor =
    alert.color === 'green'
      ? 'border-hud-green'
      : alert.color === 'cyan'
        ? 'border-hud-cyan'
        : alert.color === 'yellow'
          ? 'border-hud-yellow'
          : alert.color === 'orange'
            ? 'border-hud-orange'
            : 'border-hud-red';
  return (
    <div
      className={`rounded-lg p-4 border-2 ${borderColor} bg-black/40 font-mono ${
        flash && isCritical ? 'animate-pulse' : ''
      }`}
      style={alert.color === 'red' ? { borderColor: '#ff3366' } : undefined}
    >
      <div className="flex items-center justify-between">
        <div>
          <div
            className={`text-lg font-bold uppercase tracking-wider ${
              alert.level === 'critical'
                ? 'text-hud-red'
                : alert.level === 'warning'
                  ? 'text-hud-orange'
                  : alert.level === 'caution'
                    ? 'text-hud-yellow'
                    : alert.level === 'monitor'
                      ? 'text-hud-cyan'
                      : 'text-hud-green'
            }`}
          >
            {alert.title}
          </div>
          <div className="text-sm text-gray-300 mt-1">{alert.sub}</div>
        </div>
        {onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            className="px-3 py-1 rounded bg-white/10 text-gray-400 hover:bg-white/20 text-sm"
          >
            Dismiss
          </button>
        )}
      </div>
    </div>
  );
}
