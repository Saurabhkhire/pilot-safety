import { useEffect, useState } from 'react';
import type { PSIFeed } from '../types/feed';

const WS_URL = (() => {
  if (typeof window === 'undefined') return 'ws://localhost:8000/ws';
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = (import.meta as any).env?.VITE_WS_HOST || window.location.host;
  return `${protocol}//${host}/ws`;
})();

export function useWSFeed(): { data: PSIFeed | null; connected: boolean; error: string | null } {
  const [data, setData] = useState<PSIFeed | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ws: WebSocket | null = null;
    const connect = () => {
      try {
        ws = new WebSocket(WS_URL);
        ws.onopen = () => {
          setConnected(true);
          setError(null);
        };
        ws.onmessage = (ev) => {
          try {
            const payload = JSON.parse(ev.data as string) as PSIFeed;
            setData(payload);
          } catch {
            // ignore parse errors
          }
        };
        ws.onclose = () => {
          setConnected(false);
          ws = null;
          setTimeout(connect, 2000);
        };
        ws.onerror = () => setError('WebSocket error');
      } catch (e) {
        setError(String(e));
        setTimeout(connect, 2000);
      }
    };
    connect();
    return () => {
      if (ws) ws.close();
    };
  }, []);

  return { data, connected, error };
}
