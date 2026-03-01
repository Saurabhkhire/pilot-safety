import { useCallback, useRef, useState } from 'react';
import type { Alert } from '../types/feed';

export function useAlerts() {
  const [queue, setQueue] = useState<Array<{ id: number; alert: Alert; message?: string }>>([]);
  const idRef = useRef(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const push = useCallback((alert: Alert | null, message?: string) => {
    if (!alert) return;
    const id = ++idRef.current;
    setQueue((q) => [...q, { id, alert, message }].slice(-5));
    if (alert.level === 'caution' || alert.level === 'warning' || alert.level === 'critical') {
      try {
        if (!audioRef.current) audioRef.current = new Audio();
        // Optional: play chime — use a data URL or asset
        // audioRef.current.src = '/chime.mp3';
        // audioRef.current.play().catch(() => {});
      } catch {
        // ignore
      }
    }
  }, []);

  const dismiss = useCallback((id: number) => {
    setQueue((q) => q.filter((x) => x.id !== id));
  }, []);

  return { queue, push, dismiss };
}
