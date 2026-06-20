"""Shared REPL pane: scrollback + an input line + command history.

Both UNISHELL and Parabash are line-oriented REPLs; the only differences are
what a submitted line *does* and the title/banner. Factoring the common
scrollback, history navigation and rendering here keeps both panes tiny.
"""

from __future__ import annotations

import curses
from typing import Any

from ..render import Surface
from ..widgets import InputField, truncate
from .base import Pane

#: Maximum scrollback lines kept in memory per pane.
MAX_SCROLLBACK = 2000


class ReplPane(Pane):
    def __init__(self, pane_id: int, kind: str, title: str, prompt: str = "▸ ",
                 context: Any = None):
        super().__init__(pane_id, kind, title)
        self.context = context
        self.field = InputField(prompt=prompt)
        self.scroll: list[tuple[str, str]] = []
        self.history: list[str] = []
        self.hist_index: int | None = None
        self.view_offset = 0  # 0 == pinned to bottom

    # --- scrollback ------------------------------------------------------
    def print(self, text: str = "", role: str = "text") -> None:
        for line in str(text).split("\n"):
            self.scroll.append((line, role))
        if len(self.scroll) > MAX_SCROLLBACK:
            self.scroll = self.scroll[-MAX_SCROLLBACK:]

    def clear(self) -> None:
        self.scroll = []
        self.view_offset = 0

    # --- history ---------------------------------------------------------
    def _recall(self, direction: int) -> None:
        if not self.history:
            return
        if self.hist_index is None:
            self.hist_index = len(self.history)
        self.hist_index += direction
        if self.hist_index >= len(self.history):
            self.hist_index = None
            self.field.set("")
            return
        self.hist_index = max(0, self.hist_index)
        self.field.set(self.history[self.hist_index])

    # --- input -----------------------------------------------------------
    def handle_key(self, key: int) -> bool:
        if key == curses.KEY_UP:
            self._recall(-1)
            return True
        if key == curses.KEY_DOWN:
            self._recall(1)
            return True
        if key == curses.KEY_PPAGE:
            self.view_offset += 5
            return True
        if key == curses.KEY_NPAGE:
            self.view_offset = max(0, self.view_offset - 5)
            return True
        if key == 12:  # Ctrl-L clears
            self.clear()
            return True
        action = self.field.handle_key(key)
        if action and action[0] == "submit":
            self._submit(action[1])
        return True

    def _submit(self, text: str) -> None:
        text = text.rstrip()
        self.field.clear()
        self.view_offset = 0
        self.hist_index = None
        if not text:
            return
        self.history.append(text)
        self.run(text)

    def run(self, text: str) -> None:  # pragma: no cover - overridden
        """Execute a submitted line. Subclasses implement."""

    # --- rendering -------------------------------------------------------
    def title_text(self) -> str:
        return self.title

    def render(self, surface: Surface, focused: bool) -> None:
        if surface.profile.show_borders:
            border = "border_focus" if focused else "border"
            surface.box(role=border, title=self.title_text())
            body = surface.interior(1)
        else:
            surface.text(0, 0, self.title_text().ljust(surface.width),
                         role="tab_active" if focused else "title")
            body = Surface(surface.win, surface.rect.inset(top=1), surface.colors,
                           surface.theme, surface.profile)
        if body.height < 1:
            return
        input_row = body.height - 1
        avail = body.height - 1
        # Clamp the scrollback view.
        max_offset = max(0, len(self.scroll) - avail)
        self.view_offset = min(self.view_offset, max_offset)
        end = len(self.scroll) - self.view_offset
        start = max(0, end - avail)
        for i, (text, role) in enumerate(self.scroll[start:end]):
            body.text(i, 0, truncate(text, body.width), role=role)
        # Input line (with a scroll indicator when not pinned to the bottom).
        if self.view_offset > 0:
            body.text(input_row, 0, truncate(f"-- scrolled {self.view_offset} --", body.width),
                      role="warn")
        else:
            self.field.render(body, input_row, focused=focused)
