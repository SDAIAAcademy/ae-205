"""Configuration from the environment: nothing secret is written into the code or the image."""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass, field


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def _secret(name: str) -> str:
    """A secret comes from the environment, or from a file the runtime mounts (RIFD_LOOKUP_KEY_FILE)."""
    if os.environ.get(name):
        return os.environ[name]
    path = Path(os.environ.get(name + "_FILE", "secrets/lookup.key"))
    return path.read_text(encoding="utf-8").strip() if path.is_file() else ""


@dataclass(frozen=True)
class Settings:
    service: str = field(default_factory=lambda: _env("RIFD_SERVICE", "farz"))
    model_dir: str = field(default_factory=lambda: _env("RIFD_MODEL_DIR", "models/farz-1.0.0"))
    similar_dir: str = field(default_factory=lambda: _env("RIFD_SIMILAR_DIR", "models/shabih-1.0.0"))
    lookup_key: str = field(default_factory=lambda: _secret("RIFD_LOOKUP_KEY"))
    lookup_ms: float = field(default_factory=lambda: float(_env("RIFD_LOOKUP_MS", "120")))
    log_file: str = field(default_factory=lambda: _env("RIFD_LOG_FILE"))
    trace_file: str = field(default_factory=lambda: _env("RIFD_TRACE_FILE"))
    version_label: str = field(default_factory=lambda: _env("RIFD_RELEASE", ""))


def load() -> Settings:
    return Settings()
