-- EngageIQ Flight Deck — session and pilot profile storage

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at REAL NOT NULL,
    ended_at REAL,
    pilot_id TEXT,
    aircraft_type TEXT,
    phase_at_end TEXT
);

CREATE TABLE IF NOT EXISTS pilot_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pilot_id TEXT UNIQUE NOT NULL,
    calibration_json TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    ts REAL NOT NULL,
    event_type TEXT NOT NULL,
    payload_json TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_events_session_ts ON events(session_id, ts);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
