"""``neofetch`` for E-Console: ASCII logo + system info, fully configurable.

Kept curses-free so it can be unit-tested headlessly. The TUI app
(:mod:`econsole.apps.neofetch`) reuses :func:`gather` and the logos for a rich,
colourful, side-by-side render with the classic colour-block row; the
``neofetch`` command reuses :func:`render_text` for a clean inline dump.

Everything is driven by the ``neofetch`` section of the config, so the look can
be adjusted (which fields, which logo, colour blocks on/off) and persisted.
"""

from __future__ import annotations

import getpass
import os
import platform
import shutil
import socket
from typing import Any

from .version import banner_version

# Canonical field order. Each entry is (key, label). The Packages field is off
# by default because counting dpkg entries can be slow on a cold cache.
ALL_FIELDS: list[tuple[str, str]] = [
    ("os", "OS"), ("host", "Host"), ("kernel", "Kernel"), ("uptime", "Uptime"),
    ("shell", "Shell"), ("resolution", "Resolution"), ("profile", "Profile"),
    ("theme", "Theme"), ("panes", "Panes"), ("apps", "Apps"),
    ("commands", "Commands"), ("packages", "Packages"), ("cpu", "CPU"),
    ("memory", "Memory"), ("python", "Python"), ("firewall", "Firewall"),
]
FIELD_LABELS = dict(ALL_FIELDS)
DEFAULT_DISABLED = ["packages"]

# ---------------------------------------------------------------------------
# ASCII / Unicode logos
# ---------------------------------------------------------------------------
LOGOS: dict[str, list[str]] = {
    "econsole": [
        "  ┌──────────────┐",
        "  │ ▸ UNISHELL    │",
        "  │ $ _           │",
        "  │               │",
        "  │  E·CONSOLE OS │",
        "  └──────────────┘",
    ],
    "ascii": [
        "  +--------------+",
        "  | > UNISHELL   |",
        "  | $ _          |",
        "  |  E-CONSOLE   |",
        "  +--------------+",
    ],
    "blocks": [
        "  ███████ ",
        "  ██      ",
        "  █████   ",
        "  ██      ",
        "  ███████ ",
        "  E-CONSOLE",
    ],
    "pi": [
        "   .~~.   .~~.",
        "  '. \\/ \\/ .'",
        "   .~ .~~. ~.",
        "  : .~.''.~. :",
        "  ~ (    ) ~",
        "   ( '~~' )",
        "    '~~~~'",
    ],
}
LOGO_NAMES = list(LOGOS.keys())


def pick_logo(cfg: dict, context: Any = None) -> list[str]:
    name = cfg.get("logo", "auto")
    if name == "auto":
        name = "ascii" if (context and getattr(context, "theme", None)
                           and context.theme.high_contrast) else "econsole"
    return LOGOS.get(name, LOGOS["econsole"])


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------
def config_for(context: Any) -> dict:
    """Return the effective neofetch config (with defaults filled in)."""
    raw = {}
    if context is not None and getattr(context, "config", None):
        raw = context.config.get("neofetch") or {}
    return {
        "logo": raw.get("logo", "auto"),
        "color_blocks": raw.get("color_blocks", True),
        "disabled": list(raw.get("disabled_fields", list(DEFAULT_DISABLED))),
    }


def save_config(context: Any, cfg: dict) -> None:
    if context is not None and getattr(context, "config", None):
        context.config.set("neofetch", {
            "logo": cfg.get("logo", "auto"),
            "color_blocks": cfg.get("color_blocks", True),
            "disabled_fields": list(cfg.get("disabled", [])),
        })


# ---------------------------------------------------------------------------
# system info gatherers (all best-effort, never raise)
# ---------------------------------------------------------------------------
def _read(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return ""


def _os() -> str:
    text = _read("/etc/os-release")
    for line in text.splitlines():
        if line.startswith("PRETTY_NAME="):
            return line.split("=", 1)[1].strip().strip('"')
    return f"{platform.system()} {platform.release()}".strip() or "Linux"


def _host() -> str:
    model = _read("/proc/device-tree/model").replace("\x00", "").strip()
    if model:
        return model
    product = _read("/sys/devices/virtual/dmi/id/product_name").strip()
    if product and product.lower() not in ("", "to be filled by o.e.m."):
        return product
    return socket.gethostname() or platform.node() or "unknown"


def _uptime() -> str:
    text = _read("/proc/uptime")
    try:
        secs = int(float(text.split()[0]))
    except (ValueError, IndexError):
        return "n/a"
    days, rem = divmod(secs, 86400)
    hours, rem = divmod(rem, 3600)
    mins = rem // 60
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{mins}m")
    return " ".join(parts)


def _resolution() -> str:
    size = shutil.get_terminal_size((80, 24))
    return f"{size.columns}x{size.lines}"


def _cpu() -> str:
    text = _read("/proc/cpuinfo")
    model = None
    cores = 0
    for line in text.splitlines():
        if line.startswith("processor"):
            cores += 1
        elif model is None and (line.startswith("model name") or line.startswith("Model")
                                or line.startswith("Hardware")):
            model = line.split(":", 1)[1].strip()
    if model is None:
        model = platform.processor() or platform.machine() or "unknown"
    return f"{model} ({cores})" if cores else model


def _memory() -> str:
    text = _read("/proc/meminfo")
    info = {}
    for line in text.splitlines():
        parts = line.split(":")
        if len(parts) == 2:
            info[parts[0].strip()] = parts[1].strip()

    def kb(key):
        try:
            return int(info.get(key, "0").split()[0])
        except (ValueError, IndexError):
            return 0

    total = kb("MemTotal")
    if not total:
        return "n/a"
    avail = kb("MemAvailable") or (total - kb("MemFree"))
    used = max(0, total - avail)
    return f"{used // 1024}MiB / {total // 1024}MiB"


def _packages() -> str:
    info_dir = "/var/lib/dpkg/info"
    try:
        n = sum(1 for f in os.listdir(info_dir) if f.endswith(".list"))
        return f"{n} (dpkg)" if n else "n/a"
    except OSError:
        return "n/a"


def _apps_count() -> int:
    try:
        from . import apps
        return len(apps.APPS)
    except Exception:  # noqa: BLE001
        return 0


def gather(context: Any = None, cfg: dict | None = None) -> list[tuple[str, str]]:
    """Return ``[(label, value)]`` for the enabled fields, in canonical order."""
    cfg = cfg or config_for(context)
    disabled = set(cfg.get("disabled", []))

    values = {
        "os": _os,
        "host": _host,
        "kernel": lambda: platform.release() or "n/a",
        "uptime": _uptime,
        "shell": banner_version,
        "resolution": _resolution,
        "profile": lambda: getattr(getattr(context, "profile", None), "name", "—"),
        "theme": lambda: getattr(getattr(context, "theme", None), "name", "—"),
        "panes": lambda: str(len(context.manager.panes)) if context else "—",
        "apps": lambda: str(_apps_count()),
        "commands": lambda: str(len(context.registry.all())) if context else "—",
        "packages": _packages,
        "cpu": _cpu,
        "memory": _memory,
        "python": platform.python_version,
        "firewall": lambda: ("on" if context and context.config.get("firewall_enabled")
                             else ("off" if context else "—")),
    }
    out = []
    for key, label in ALL_FIELDS:
        if key in disabled:
            continue
        try:
            out.append((label, str(values[key]())))
        except Exception:  # noqa: BLE001 - a bad probe must not break neofetch
            out.append((label, "n/a"))
    return out


def title_line(context: Any = None) -> str:
    try:
        user = (context.config.get("current_user") if context else None) or getpass.getuser()
    except Exception:  # noqa: BLE001
        user = "user"
    return f"{user}@{_host_short()}"


def _host_short() -> str:
    return (socket.gethostname() or "econsole").split(".")[0]


# Color-block row: the eight base ANSI colours (indices 0..7).
COLOR_BLOCK_INDICES = list(range(8))


def render_text(context: Any = None, cfg: dict | None = None) -> list[tuple[str, str]]:
    """Render a stacked, single-colour-per-line fetch for the shell scrollback."""
    cfg = cfg or config_for(context)
    lines: list[tuple[str, str]] = []
    for row in pick_logo(cfg, context):
        lines.append((row, "accent"))
    lines.append(("", "text"))
    title = title_line(context)
    lines.append((title, "accent"))
    lines.append(("─" * len(title), "dim"))
    for label, value in gather(context, cfg):
        lines.append((f"{label}: {value}", "text"))
    if cfg.get("color_blocks", True):
        lines.append(("", "text"))
        lines.append(("███▓▓▒▒░░  ░░▒▒▓▓███", "accent2"))
    return lines
