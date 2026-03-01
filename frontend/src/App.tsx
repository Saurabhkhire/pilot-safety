import React, { useEffect } from 'react';
import { useWSFeed } from './hooks/useWSFeed';
import { useAlerts } from './hooks/useAlerts';
import { PSIRing } from './components/PSIRing';
import { SignalGrid } from './components/SignalGrid';
import { VitalsStrip } from './components/VitalsStrip';
import { LandingReport } from './components/LandingReport';
import { AgentFeed } from './components/AgentFeed';
import { ErrorLog } from './components/ErrorLog';
import { AlertBanner } from './components/AlertBanner';
import { PSITimeline } from './components/PSITimeline';
import { SimulatorPanel } from './components/SimulatorPanel';

function App() {
  const { data, connected, error } = useWSFeed();
  const { queue, push, dismiss } = useAlerts();

  useEffect(() => {
    if (data?.alert) push(data.alert);
  }, [data?.alert, push]);

  return (
    <div className="min-h-screen bg-slate-950 text-white p-4 font-sans">
      {/* Header + why on-device */}
      <header className="mb-4 flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-3">
        <h1 className="font-display text-xl font-bold tracking-wider text-hud-cyan">
          EngageIQ Flight Deck
        </h1>
        <div className="flex items-center gap-3 text-sm">
          <span
            className={`inline-block w-2 h-2 rounded-full ${
              connected ? 'bg-hud-green' : 'bg-hud-red'
            }`}
          />
          {connected ? 'Live' : 'Disconnected'}
          {error && <span className="text-hud-orange">{error}</span>}
        </div>
      </header>

      <section className="mb-4 p-3 rounded bg-hud-panel border border-white/10 text-xs text-gray-400 max-w-2xl">
        <strong className="text-gray-300">Why on-device:</strong> Pilot biometric video cannot leave the aircraft (privacy). Alert latency &lt;500ms — cloud round-trip impossible at cruise. Oceanic routes have zero connectivity. Continuous camera feed economics don&apos;t work with per-call API pricing.
      </section>

      {/* Alert queue */}
      {queue.length > 0 && (
        <div className="mb-4 space-y-2">
          {queue.map(({ id, alert }) => (
            <AlertBanner key={id} alert={alert} onDismiss={() => dismiss(id)} flash={alert.level === 'critical'} />
          ))}
        </div>
      )}

      {/* Main HUD */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="flex flex-col items-center gap-4">
          <PSIRing psi={data?.psi ?? 100} size={220} strokeWidth={16} />
          <PSITimeline currentPsi={data?.psi ?? 100} maxPoints={80} />
        </div>
        <div className="space-y-4">
          <VitalsStrip data={data ?? null} />
          <SignalGrid signals={data?.signals ?? {}} pilot_state={data?.pilot_state ?? null} />
          <AlertBanner alert={data?.alert ?? null} />
        </div>
        <div className="space-y-4">
          <AgentFeed actions={data?.agent_actions ?? []} />
          <ErrorLog errors={data?.cockpit_errors ?? []} />
          <LandingReport landing={data?.landing ?? null} />
        </div>
      </div>

      <SimulatorPanel />
    </div>
  );
}

export default App;
