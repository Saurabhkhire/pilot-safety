import React, { useCallback, useEffect, useRef, useState } from 'react';

// Use relative URL so Vite proxy forwards /test to backend (avoids 404)
function getApiBase(): string {
  if (typeof window === 'undefined') return '';
  const base = (import.meta as any).env?.VITE_API_URL;
  return base ? base.replace(/\/$/, '') : '';
}

const HINT = 'drowsy.png → WARNING, critical.jpg → CRITICAL, landing.png, cockpit.jpg';

export const ScenarioImagePanel: React.FC = () => {
  const [visible, setVisible] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [removing, setRemoving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [images, setImages] = useState<string[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(() => {
    const base = getApiBase();
    fetch(base ? `${base}/test/scenario-images` : '/test/scenario-images')
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data?.images)) setImages(data.images);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (visible) refresh();
  }, [visible, refresh]);

  const upload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const form = new FormData();
      form.append('file', file);
      const base = getApiBase();
      const r = await fetch(base ? `${base}/test/upload-scenario-image` : '/test/upload-scenario-image', { method: 'POST', body: form });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) {
        const msg = r.status === 404
          ? 'Backend route not found. Start backend: cd backend && uvicorn main:app --port 8000'
          : (data?.detail || `HTTP ${r.status}`);
        setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
        return;
      }
      refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  }, [refresh]);

  const remove = useCallback(async (filename: string) => {
    const scenario = filename.replace(/\.(png|jpg|jpeg|jpe|webp)$/i, '');
    setRemoving(scenario);
    setError(null);
    try {
      const base = getApiBase();
      const url = base ? `${base}/test/scenario-image?scenario=${encodeURIComponent(scenario)}` : `/test/scenario-image?scenario=${encodeURIComponent(scenario)}`;
      const r = await fetch(url, {
        method: 'DELETE',
      });
      if (!r.ok) {
        const data = await r.json().catch(() => ({}));
        setError(data?.detail || `HTTP ${r.status}`);
        return;
      }
      refresh();
    } finally {
      setRemoving(null);
    }
  }, [refresh]);

  return (
    <>
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        className="fixed top-52 right-0 z-50 px-3 py-2 rounded-l-lg bg-slate-800 border border-r-0 border-white/20 text-xs font-mono text-gray-300 hover:bg-slate-700 hover:text-white shadow-lg transition-colors"
        title={visible ? 'Hide upload' : 'Show upload'}
      >
        {visible ? '▶ Hide' : '◀ Upload'}
      </button>

      {visible && (
        <div className="fixed top-52 right-0 z-40 w-72 bg-slate-900/98 border border-white/20 rounded-l-lg shadow-xl font-mono text-sm">
          <div className="flex items-center justify-between p-2 border-b border-white/10">
            <span className="text-hud-cyan font-semibold">Upload scenario image</span>
            <button type="button" onClick={() => setVisible(false)} className="text-gray-400 hover:text-white p-1 rounded" aria-label="Close">×</button>
          </div>
          <div className="p-3 space-y-3">
            {error && <div className="text-hud-red text-xs bg-red-900/30 rounded p-2">{error}</div>}

            <input ref={fileRef} type="file" accept=".png,.jpg,.jpeg,.jpe,.webp,image/png,image/jpeg,image/webp" className="hidden" onChange={upload} />
            <button
              type="button"
              disabled={uploading}
              onClick={() => fileRef.current?.click()}
              className="w-full px-3 py-2 rounded bg-slate-800 hover:bg-slate-700 border border-white/10 text-xs disabled:opacity-50"
            >
              {uploading ? 'Uploading…' : 'Upload (drowsy.png, critical.jpg, etc.)'}
            </button>
            <div className="text-xs text-gray-500">{HINT}</div>

            {images.length > 0 && (
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">Uploaded</div>
                <ul className="space-y-1">
                  {images.map((name) => (
                    <li key={name} className="flex items-center justify-between gap-2 px-2 py-1 rounded bg-slate-800">
                      <span className="text-xs truncate">{name}</span>
                      <button
                        type="button"
                        disabled={removing !== null}
                        onClick={() => remove(name)}
                        className="shrink-0 px-2 py-0.5 rounded text-hud-red hover:bg-red-900/30 text-xs disabled:opacity-50"
                      >
                        {removing === name.replace(/\.[^.]+$/, '') ? '…' : 'Remove'}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};
