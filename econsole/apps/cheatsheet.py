"""Hotkey Cheatsheet app: hotkeys and commands in one scrollable reference."""

from __future__ import annotations

import curses
from typing import Any

from ..hotkeys import by_category
from ..widgets import truncate
from .base import AppPane


class CheatsheetApp(AppPane):
    app_name = "cheatsheet"
    app_label = "Hotkey Cheatsheet"

    def __init__(self, pane_id: int = 0, context: Any = None):
        super().__init__(pane_id, context)
        self.offset = 0

    def status_hint(self) -> str:
        return "↑↓ scroll"

    def _lines(self) -> list[tuple[str, str]]:
        """Return ``(text, role)`` rows for the whole reference."""
        rows: list[tuple[str, str]] = []
        for category, keys in by_category().items():
            rows.append((category.upper(), "accent"))
            for key in keys:
                rows.append((f"  {key.combo:<22} {key.description}", "text"))
            rows.append(("", "text"))

        rows.append(("COMMANDS", "accent"))
        if self.context and getattr(self.context, "registry", None):
            for category, commands in self.context.registry.categories().items():
                rows.append((f"  {category}", "dim"))
                for command in commands:
                    rows.append((f"    {command.help_line()}", "text"))
        return rows

    def handle_key(self, key: int) -> bool:
        if key in (curses.KEY_UP, ord("k")):
            self.offset = max(0, self.offset - 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            self.offset += 1
        elif key == curses.KEY_NPAGE:
            self.offset += 10
        elif key == curses.KEY_PPAGE:
            self.offset = max(0, self.offset - 10)
        elif key in (curses.KEY_HOME, ord("g")):
            self.offset = 0
        else:
            return False
        return True

    def render_body(self, surface, focused: bool) -> None:
        lines = self._lines()
        max_offset = max(0, len(lines) - surface.height)
        self.offset = min(self.offset, max_offset)
        view = lines[self.offset:self.offset + surface.height]
        for i, (text, role) in enumerate(view):
            surface.text(i, 0, truncate(text, surface.width), role=role)
