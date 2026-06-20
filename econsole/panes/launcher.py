"""App Launcher pane.

A single-layer command palette: it lists the available apps and opens the
selected one, then closes itself. Because the window model has no overlays, the
launcher is a normal pane rather than a floating dialog.
"""

from __future__ import annotations

import curses
from typing import Any

from ..render import Surface
from ..widgets import truncate
from .base import Pane


class LauncherPane(Pane):
    def __init__(self, pane_id: int = 0, context: Any = None):
        super().__init__(pane_id, kind="launcher", title="App Launcher")
        self.context = context
        self.selected = 0

    def _apps(self):
        from ..apps import APPS
        return list(APPS.values())

    def status_hint(self) -> str:
        return "↑↓ select · Enter=open · Esc=close"

    def handle_key(self, key: int) -> bool:
        apps = self._apps()
        if key in (curses.KEY_UP, ord("k")):
            self.selected = max(0, self.selected - 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            self.selected = min(len(apps) - 1, self.selected + 1)
        elif key in (curses.KEY_ENTER, 10, 13):
            if self.context and apps:
                name = apps[self.selected].name
                self.context.close_pane(self.id)
                self.context.open_app(name)
        elif key in (27, ord("q")):
            if self.context:
                self.context.close_pane(self.id)
        else:
            return False
        return True

    def render(self, surface: Surface, focused: bool) -> None:
        border = "border_focus" if focused else "border"
        if surface.profile.show_borders:
            surface.box(role=border, title="App Launcher")
            body = surface.interior(1)
        else:
            surface.text(0, 0, "App Launcher".ljust(surface.width), role="title")
            body = Surface(surface.win, surface.rect.inset(top=1), surface.colors,
                           surface.theme, surface.profile)
        apps = self._apps()
        self.selected = max(0, min(len(apps) - 1, self.selected))
        for i, info in enumerate(apps):
            if i >= body.height:
                break
            selected = i == self.selected
            prefix = "▸ " if selected else "  "
            line = f"{prefix}{info.label:<18} {truncate(info.description, max(0, body.width - 22))}"
            body.text(i, 0, line, role="selection" if (selected and focused) else "text")
