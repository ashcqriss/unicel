"""Base class for app panes.

Handles the shared chrome (border + title in normal density, a single title
line in compact/AR density) and a scrolling-list selection helper, so concrete
apps only implement :meth:`render_body` and their own key handling.
"""

from __future__ import annotations

from typing import Any

from ..panes.base import Pane
from ..render import Surface


class AppPane(Pane):
    app_name = "app"
    app_label = "App"

    def __init__(self, pane_id: int = 0, context: Any = None):
        super().__init__(pane_id, kind=self.app_name, title=self.app_label)
        self.context = context
        self.selected = 0

    # --- chrome ----------------------------------------------------------
    def header_title(self, focused: bool) -> str:
        return self.app_label

    def render(self, surface: Surface, focused: bool) -> None:
        if surface.profile.show_borders:
            border = "border_focus" if focused else "border"
            surface.box(role=border, title=self.header_title(focused))
            body = surface.interior(1)
        else:
            # Compact / AR: a single accented title line, no border.
            surface.text(0, 0, self.header_title(focused).ljust(surface.width),
                         role="tab_active" if focused else "title")
            body = Surface(surface.win, surface.rect.inset(top=1), surface.colors,
                           surface.theme, surface.profile)
        if body.height > 0:
            self.render_body(body, focused)

    def render_body(self, surface: Surface, focused: bool) -> None:  # pragma: no cover
        """Draw the app contents into the interior surface."""

    # --- selection helper -----------------------------------------------
    def move_selection(self, delta: int, count: int) -> None:
        if count <= 0:
            self.selected = 0
            return
        self.selected = max(0, min(count - 1, self.selected + delta))

    def clamp_selection(self, count: int) -> None:
        if count <= 0:
            self.selected = 0
        else:
            self.selected = max(0, min(count - 1, self.selected))

    def visible_window(self, count: int, height: int) -> tuple[int, int]:
        """Return ``(start, end)`` indices to keep ``selected`` on screen."""
        if height <= 0 or count <= 0:
            return (0, 0)
        start = 0
        if self.selected >= height:
            start = self.selected - height + 1
        start = max(0, min(start, max(0, count - height)))
        return (start, min(count, start + height))
