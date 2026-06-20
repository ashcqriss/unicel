"""Firewall Panel.

A management/visualisation panel for the host firewall. The spec wants the
firewall "enabled by default" with a default-deny posture. This panel models
that policy and a rule set and persists it; on a real E-Console image the same
rules would be rendered to an ``nftables`` ruleset by the system layer (see
docs/SECURITY.md). Inside this prototype it is a faithful, editable model rather
than a live packet filter.
"""

from __future__ import annotations

import curses
from typing import Any

from ..config import JsonStore, data_dir
from ..widgets import truncate
from .base import AppPane

_DEFAULT_RULES = [
    {"id": 1, "action": "allow", "dir": "in", "proto": "any", "port": "lo",
     "desc": "Loopback interface", "enabled": True},
    {"id": 2, "action": "allow", "dir": "in", "proto": "any", "port": "established",
     "desc": "Established/related connections", "enabled": True},
    {"id": 3, "action": "allow", "dir": "in", "proto": "tcp", "port": "22",
     "desc": "SSH remote access", "enabled": True},
    {"id": 4, "action": "allow", "dir": "out", "proto": "tcp", "port": "80,443",
     "desc": "HTTP/HTTPS (web, apt, updates)", "enabled": True},
    {"id": 5, "action": "allow", "dir": "out", "proto": "udp", "port": "53",
     "desc": "DNS resolution", "enabled": True},
    {"id": 6, "action": "deny", "dir": "in", "proto": "any", "port": "any",
     "desc": "Default: drop all other inbound", "enabled": True},
]


class FirewallStore(JsonStore):
    def __init__(self):
        super().__init__(data_dir() / "firewall.json",
                         default={"rules": [dict(r) for r in _DEFAULT_RULES]})

    @property
    def rules(self):
        return self.data.setdefault("rules", [])


class FirewallApp(AppPane):
    app_name = "firewall"
    app_label = "Firewall Panel"

    def __init__(self, pane_id: int = 0, context: Any = None):
        super().__init__(pane_id, context)
        self.store = FirewallStore()

    def _enabled(self) -> bool:
        return bool(self.context.config.get("firewall_enabled")) if self.context else True

    def header_title(self, focused: bool) -> str:
        state = "ENABLED" if self._enabled() else "DISABLED"
        return f"Firewall — {state}"

    def status_hint(self) -> str:
        return "↑↓ select · Space=toggle rule · e=enable/disable firewall"

    def handle_key(self, key: int) -> bool:
        rules = self.store.rules
        if key in (curses.KEY_UP, ord("k")):
            self.move_selection(-1, len(rules))
        elif key in (curses.KEY_DOWN, ord("j")):
            self.move_selection(1, len(rules))
        elif key in (ord(" "), curses.KEY_ENTER, 10, 13):
            if rules:
                rules[self.selected]["enabled"] = not rules[self.selected]["enabled"]
                self.store.save()
        elif key in (ord("e"), ord("E")):
            if self.context:
                self.context.config.set("firewall_enabled", not self._enabled())
        else:
            return False
        return True

    def render_body(self, surface, focused: bool) -> None:
        enabled = self._enabled()
        surface.text(0, 0, "Default policy:", role="dim")
        surface.text(0, 16, "INPUT DROP · OUTPUT ACCEPT · FORWARD DROP",
                     role="ok" if enabled else "warn")
        surface.text(1, 0, "Status:", role="dim")
        surface.text(1, 16, "active (default-deny inbound)" if enabled else "INACTIVE — host exposed",
                     role="ok" if enabled else "error")
        surface.hline(2)
        surface.text(3, 0, "RULES", role="accent")

        rules = self.store.rules
        self.clamp_selection(len(rules))
        start_row = 4
        for i, rule in enumerate(rules):
            row = start_row + i
            if row >= surface.height:
                break
            selected = i == self.selected
            check = "✓" if rule["enabled"] else "✗"
            action = rule["action"].upper()
            spec = f"{rule['dir']:<3} {rule['proto']:<4} {rule['port']:<12}"
            prefix = "▸" if selected else " "
            line = f"{prefix}{check} {action:<5} {spec} {rule['desc']}"
            role = "selection" if (selected and focused) else (
                "ok" if rule["action"] == "allow" else "warn")
            if not rule["enabled"]:
                role = "dim"
            surface.text(row, 0, truncate(line, surface.width), role=role)
