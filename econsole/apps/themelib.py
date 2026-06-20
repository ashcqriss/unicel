"""Theme Library app: browse and apply themes with a live preview swatch."""

from __future__ import annotations

import curses
from typing import Any

from ..theme import list_themes
from ..widgets import truncate
from .base import AppPane


class ThemeLibraryApp(AppPane):
    app_name = "themes"
    app_label = "Theme Library"

    def __init__(self, pane_id: int = 0, context: Any = None):
        super().__init__(pane_id, context)
        self.themes = list_themes()

    def status_hint(self) -> str:
        return "↑↓ select · Enter=apply"

    def handle_key(self, key: int) -> bool:
        if key in (curses.KEY_UP, ord("k")):
            self.move_selection(-1, len(self.themes))
        elif key in (curses.KEY_DOWN, ord("j")):
            self.move_selection(1, len(self.themes))
        elif key in (curses.KEY_ENTER, 10, 13, ord(" ")):
            if self.context:
                self.context.set_theme(self.themes[self.selected].name)
        else:
            return False
        return True

    def render_body(self, surface, focused: bool) -> None:
        self.clamp_selection(len(self.themes))
        current = self.context.theme.name if self.context else None
        for i, theme in enumerate(self.themes):
            if i >= surface.height:
                break
            selected = i == self.selected
            mark = "●" if theme.name == current else " "
            prefix = "▸" if selected else " "
            line = f"{prefix}{mark} {truncate(theme.label, 18):<18} {theme.profile_hint:<8}"
            surface.text(i, 0, line, role="selection" if (selected and focused) else "text")
            # description on the right if room
            if surface.width > 48:
                surface.text(i, 40, truncate(theme.description, surface.width - 40), role="dim")
