"""Configuration and persistent state for E-Console.

Everything is stored as JSON under the XDG base directories so the core system
image can stay read-only while user state lives in a writable overlay. No
third-party dependencies: just :mod:`json` and :mod:`pathlib`.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def _xdg(base_env: str, default: str) -> Path:
    raw = os.environ.get(base_env)
    root = Path(raw) if raw else Path.home() / default
    return root / "econsole"


def config_dir() -> Path:
    """Return ``$XDG_CONFIG_HOME/econsole`` (default ``~/.config/econsole``)."""
    return _xdg("XDG_CONFIG_HOME", ".config")


def data_dir() -> Path:
    """Return ``$XDG_DATA_HOME/econsole`` (default ``~/.local/share/econsole``)."""
    return _xdg("XDG_DATA_HOME", ".local/share")


def _atomic_write(path: Path, text: str) -> None:
    """Write ``text`` to ``path`` atomically to avoid half-written state files."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


class JsonStore:
    """A tiny JSON-backed document store.

    Used as the base for every persistent app store (notes, tasks, activity,
    users, ...). Keeps the data in memory and flushes to disk on :meth:`save`.
    """

    def __init__(self, path: Path, default: Any | None = None):
        self.path = Path(path)
        self._default = default if default is not None else {}
        self.data: Any = self._load()

    def _load(self) -> Any:
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except FileNotFoundError:
            return json.loads(json.dumps(self._default))  # deep copy of default
        except (json.JSONDecodeError, OSError):
            # Corrupt or unreadable state should never crash the shell; fall
            # back to defaults and let the next save heal the file.
            return json.loads(json.dumps(self._default))

    def save(self) -> None:
        _atomic_write(self.path, json.dumps(self.data, indent=2, ensure_ascii=False))


class Config(JsonStore):
    """Top-level shell settings (active profile, theme, current user, ...)."""

    DEFAULTS: dict[str, Any] = {
        "profile": "desktop",
        "theme": "econsole-dark",
        "current_user": None,
        "first_run": True,
        "show_clock": True,
        "firewall_enabled": True,
        "auto_update": True,
        "neofetch": {
            "logo": "auto",
            "color_blocks": True,
            "disabled_fields": ["packages"],
        },
    }

    def __init__(self, path: Path | None = None):
        super().__init__(path or (config_dir() / "config.json"), default=dict(self.DEFAULTS))
        # Backfill any keys added in newer versions.
        changed = False
        for key, value in self.DEFAULTS.items():
            if key not in self.data:
                self.data[key] = value
                changed = True
        if changed:
            self.save()

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.save()
