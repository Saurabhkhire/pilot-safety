"""EngageIQ Flight Deck — runtime configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    """App configuration from env with defaults."""

    # Ollama
    ollama_host: str = field(default_factory=lambda: os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    ollama_perception_model: str = field(default_factory=lambda: os.getenv("OLLAMA_PERCEPTION", "gemma3n"))
    ollama_action_model: str = field(default_factory=lambda: os.getenv("OLLAMA_ACTION", "functiongemma"))
    ollama_landing_model: str = field(default_factory=lambda: os.getenv("OLLAMA_LANDING", "gemma3n"))

    # Cameras (device indices or paths)
    camera_face_index: int = field(default_factory=lambda: int(os.getenv("CAMERA_FACE", "0")))
    camera_external_index: int = field(default_factory=lambda: int(os.getenv("CAMERA_EXTERNAL", "1")))

    # PSI / polling
    psi_poll_hz: float = 2.0
    ws_broadcast_hz: float = 2.0

    # Paths
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", "engageiq.db"))
    replay_json_path: str = field(default_factory=lambda: os.getenv("REPLAY_JSON", ""))

    def __post_init__(self) -> None:
        self.psi_interval_sec = 1.0 / self.psi_poll_hz
        self.ws_interval_sec = 1.0 / self.ws_broadcast_hz


config = Config()
