"""File Manager: a read-only filesystem browser (an ``lf``-style pane)."""

from __future__ import annotations

import curses
import os
from pathlib import Path
from typing import Any

from ..widgets import truncate
from .base import AppPane


def _human_size(num: int) -> str:
    size = float(num)
    for unit in ("B", "K", "M", "G", "T"):
        if size < 1024 or unit == "T":
            return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}T"


class FileManagerApp(AppPane):
    app_name = "files"
    app_label = "File Manager"

    def __init__(self, pane_id: int = 0, context: Any = None, path: str | None = None):
        super().__init__(pane_id, context)
        self.path = Path(path).expanduser() if path else Path.home()
        self.error = ""

    def header_title(self, focused: bool) -> str:
        return f"Files — {truncate(str(self.path), 40)}"

    def status_hint(self) -> str:
        return "↑↓ select · Enter/→ open · ←/u up · h=home"

    def _entries(self) -> list[Path]:
        try:
            children = sorted(
                self.path.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
            self.error = ""
        except (PermissionError, OSError) as exc:
            self.error = str(exc)
            children = []
        entries: list[Path] = []
        if self.path != self.path.parent:
            entries.append(self.path.parent)  # ".."
        entries.extend(children)
        return entries

    def handle_key(self, key: int) -> bool:
        entries = self._entries()
        if key in (curses.KEY_UP, ord("k")):
            self.move_selection(-1, len(entries))
        elif key in (curses.KEY_DOWN, ord("j")):
            self.move_selection(1, len(entries))
        elif key in (curses.KEY_ENTER, 10, 13, curses.KEY_RIGHT, ord("l")):
            self._open(entries)
        elif key in (curses.KEY_LEFT, ord("u"), curses.KEY_BACKSPACE, 127):
            self._go(self.path.parent)
        elif key in (ord("h"), ord("~")):
            self._go(Path.home())
        else:
            return False
        return True

    def _open(self, entries: list[Path]) -> None:
        if not entries:
            return
        target = entries[self.selected]
        if self.selected == 0 and target == self.path.parent:
            self._go(target)
        elif target.is_dir():
            self._go(target)
        # files: selection stays; preview shown in render

    def _go(self, path: Path) -> None:
        try:
            if path.is_dir():
                self.path = path.resolve()
                self.selected = 0
        except OSError as exc:
            self.error = str(exc)

    def render_body(self, surface, focused: bool) -> None:
        entries = self._entries()
        self.clamp_selection(len(entries))
        if self.error:
            surface.text(0, 0, truncate(f"⚠ {self.error}", surface.width), role="error")
        start, end = self.visible_window(len(entries), surface.height - 1)
        for row, idx in enumerate(range(start, end)):
            entry = entries[idx]
            selected = idx == self.selected
            is_parent = idx == 0 and entry == self.path.parent
            name = ".." if is_parent else entry.name
            try:
                is_dir = entry.is_dir()
                size = "" if is_dir else _human_size(entry.stat().st_size)
            except OSError:
                is_dir, size = False, "?"
            icon = "📁" if is_dir else "  "
            display = f"{name}/" if is_dir and not is_parent else name
            prefix = "▸" if selected else " "
            line = f"{prefix}{icon} {truncate(display, max(0, surface.width - 12))}"
            surface.text(row, 0, line.ljust(max(0, surface.width - 8)),
                         role="selection" if (selected and focused) else
                         ("accent" if is_dir else "text"))
            if size:
                surface.text(row, max(0, surface.width - 7), f"{size:>6}", role="dim")
