/** WebSocket message schema — emitted every 500ms from backend */

export interface PilotState {
  state: 'ALERT' | 'FATIGUED' | 'DROWSY' | 'CRITICAL';
  perclos_est: number;
  yawn: boolean;
  head_drop: boolean;
  gaze_off_instruments: boolean;
  confidence: number;
  reason: string;
}

export interface Signals {
  yawn_count_10m?: number;
  head_drop_count_30m?: number;
  gaze_off_pct?: number;
  critical_events_1h?: number;
  fatigue_index?: string;
}

export interface CockpitError {
  ts: number;
  type: string;
  description: string;
  severity: number;
  points_deducted?: number;
}

export interface LandingEvent {
  t_ms: number;
  type: string;
}

export interface LandingReport {
  score: number;
  bounce_count?: number;
  contact_type?: string;
  on_centerline?: boolean;
  events?: LandingEvent[];
}

export interface Alert {
  level: string;
  title: string;
  color: string;
  sub: string;
}

export interface PSIFeed {
  ts: number;
  psi: number;
  phase: string;
  pilot_state: PilotState | null;
  signals: Signals;
  cockpit_errors: CockpitError[];
  landing: LandingReport | null;
  alert: Alert | null;
  agent_actions: string[];
}
