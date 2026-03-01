import React, { useCallback, useRef, useState } from 'react';

const ACCEPTED_VIDEO = '.mp4,.avi,.mov,.webm,.mkv';

function getApiBase(): string {
  if (typeof window === 'undefined') return 'http://localhost:8000';
  const base = (import.meta as any).env?.VITE_API_URL;
  return base ? base.replace(/\/$/, '') : 'http://localhost:8000';
}

export const VideoPanel: React.FC = () => {
  const [visible, setVisible] = useState(false);
  const [cam1Loading, setCam1Loading] = useState(false);
  const [cam2Loading, setCam2Loading] = useState(false);
  const [cam1Name, setCam1Name] = useState<string | null>(null);
  const [cam2Name, setCam2Name] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const cam1Ref = useRef<HTMLInputElement>(null);
  const cam2Ref = useRef<HTMLInputElement>(null);

  const upload = useCallback(async (cam: 1 | 2, file: File) => {
    const setLoading = cam === 1 ? setCam1Loading : setCam2Loading;
    const setName = cam === 1 ? setCam1Name : setCam2Name;
    const endpoint = cam === 1 ? '/test/upload-video' : '/test/upload-video-cam2';
    setLoading(true);
    setError(null);
    try {
      const form = new FormData();
      form.append('file', file);
      const r = await fetch(`${getApiBase()}${endpoint}`, { method: 'POST', body: form });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) {
        setError(data?.detail || `HTTP ${r.status}`);
        return;
      }
      setName(file.name);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed');
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(async (cam: 1 | 2) => {
    const setLoading = cam === 1 ? setCam1Loading : setCam2Loading;
    const setName = cam === 1 ? setCam1Name : setCam2Name;
    const endpoint = cam === 1 ? '/test/clear-video' : '/test/clear-video-cam2';
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`${getApiBase()}${endpoint}`, { method: 'POST' });
      if (r.ok) setName(null);
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <>
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        className="fixed top-20 right-0 z-50 px-3 py-2 rounded-l-lg bg-slate-800 border border-r-0 border-white/20 text-xs font-mono text-gray-300 hover:bg-slate-700 hover:text-white shadow-lg transition-colors"
        title={visible ? 'Hide video' : 'Show video upload'}
      >
        {visible ? '▶ Hide' : '◀ Video'}
      </button>

      {visible && (
        <div className="fixed top-20 right-0 z-40 w-72 bg-slate-900/98 border border-white/20 rounded-l-lg shadow-xl font-mono text-sm">
          <div className="flex items-center justify-between p-2 border-b border-white/10">
            <span className="text-hud-cyan font-semibold">Video feeds</span>
            <button type="button" onClick={() => setVisible(false)} className="text-gray-400 hover:text-white p-1 rounded" aria-label="Close">×</button>
          </div>
          <div className="p-3 space-y-4">
            {error && <div className="text-hud-red text-xs bg-red-900/30 rounded p-2">{error}</div>}

            {/* Camera 1 — Pilot */}
            <div>
              <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Camera 1 — Pilot (face)</div>
              <input ref={cam1Ref} type="file" accept={ACCEPTED_VIDEO} className="hidden" onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ''; if (f) upload(1, f); }} />
              <div className="flex gap-2">
                <button type="button" disabled={cam1Loading} onClick={() => cam1Ref.current?.click()} className="flex-1 px-3 py-2 rounded bg-slate-800 hover:bg-slate-700 border border-white/10 text-xs disabled:opacity-50">
                  {cam1Loading ? 'Uploading…' : cam1Name ? 'Replace' : 'Upload'}
                </button>
                {cam1Name && <button type="button" onClick={() => clear(1)} className="px-2 py-1 rounded bg-slate-700 text-xs text-gray-400 hover:text-white">Clear</button>}
              </div>
            </div>

            {/* Camera 2 — Landing / takeoff */}
            <div>
              <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Camera 2 — Landing / takeoff</div>
              <input ref={cam2Ref} type="file" accept={ACCEPTED_VIDEO} className="hidden" onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ''; if (f) upload(2, f); }} />
              <div className="flex gap-2">
                <button type="button" disabled={cam2Loading} onClick={() => cam2Ref.current?.click()} className="flex-1 px-3 py-2 rounded bg-slate-800 hover:bg-slate-700 border border-white/10 text-xs disabled:opacity-50">
                  {cam2Loading ? 'Uploading…' : cam2Name ? 'Replace' : 'Upload'}
                </button>
                {cam2Name && <button type="button" onClick={() => clear(2)} className="px-2 py-1 rounded bg-slate-700 text-xs text-gray-400 hover:text-white">Clear</button>}
              </div>
            </div>

            <div className="text-xs text-gray-500">Format: MP4, AVI, MOV, WebM, MKV</div>
          </div>
        </div>
      )}
    </>
  );
};
