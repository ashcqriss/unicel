"""Settings app: live system configuration.

Each row knows how to read its current value and how to change it. Changing the
profile or theme calls back into the shell context so the whole UI re-renders
immediately.
"""

from __future__ import annotations

import curses
from typing import Any

from ..profile import PROFILES
from ..theme import THEMES
from .base import AppPane


class _Row:
    def __init__(self, label: str, getter, cycler=None, toggler=None):
        self.label = label
        self.getter = getter
        self.cycler = cycler      # cycler(direction:int) -> None
        self.toggler = toggler    # toggler() -> None


class SettingsApp(AppPane):
    app_name = "settings"
    app_label = "Settings"

    def __init__(self, pane_id: int = 0, context: Any = None):
        super().__init__(pane_id, context)
        self.rows = self._build_rows()

    def _build_rows(self) -> list[_Row]:
        ctx = self.context
        profile_names = list(PROFILES.keys())
        theme_names = list(THEMES.keys())

        def cycle_list(names, current, direction, apply):
            if current in names:
                idx = (names.index(current) + direction) % len(names)
            else:
                idx = 0
            apply(names[idx])

        def get_profile():
            return ctx.profile.label if ctx else "—"

        def cycle_profile(direction):
            if ctx:
                cycle_list(profile_names, ctx.profile.name, direction, ctx.set_profile)

        def get_theme():
            return ctx.theme.label if ctx else "—"

        def cycle_theme(direction):
            if ctx:
                cycle_list(theme_names, ctx.theme.name, direction, ctx.set_theme)

        def toggle_cfg(key):
            if ctx:
                ctx.config.set(key, not ctx.config.get(key))

        def get_bool(key):
            return "on" if (ctx and ctx.config.get(key)) else "off"

        def get_user():
            return (ctx.config.get("current_user") or "—") if ctx else "—"

        return [
            _Row("Display profile", get_profile, cycler=cycle_profile),
            _Row("Theme", get_theme, cycler=cycle_theme),
            _Row("Show clock", lambda: get_bool("show_clock"),
                 toggler=lambda: toggle_cfg("show_clock")),
            _Row("Firewall enabled", lambda: get_bool("firewall_enabled"),
                 toggler=lambda: toggle_cfg("firewall_enabled")),
            _Row("Automatic updates", lambda: get_bool("auto_update"),
                 toggler=lambda: toggle_cfg("auto_update")),
            _Row("Current user", get_user),
        ]

    def status_hint(self) -> str:
        return "↑↓ select · ←→ change · Enter/Space toggle"

    def handle_key(self, key: int) -> bool:
        if key in (curses.KEY_UP, ord("k")):
            self.move_selection(-1, len(self.rows))
        elif key in (curses.KEY_DOWN, ord("j")):
            self.move_selection(1, len(self.rows))
        elif key == curses.KEY_LEFT:
            self._change(-1)
        elif key == curses.KEY_RIGHT:
            self._change(1)
        elif key in (ord(" "), curses.KEY_ENTER, 10, 13):
            row = self.rows[self.selected]
            if row.toggler:
                row.toggler()
            elif row.cycler:
                row.cycler(1)
        else:
            return False
        return True

    def _change(self, direction: int) -> None:
        row = self.rows[self.selected]
        if row.cycler:
            row.cycler(direction)
        elif row.toggler:
            row.toggler()

    def render_body(self, surface, focused: bool) -> None:
        self.clamp_selection(len(self.rows))
        for i, row in enumerate(self.rows):
            if i >= surface.height:
                break
            selected = i == self.selected
            prefix = "▸ " if selected else "  "
            value = row.getter()
            label = f"{prefix}{row.label}"
            surface.text(i, 0, label.ljust(max(0, surface.width - 16)),
                         role="selection" if (selected and focused) else "text")
            surface.text(i, max(0, surface.width - 14), f"‹ {value} ›",
                         role="accent" if selected else "dim")
