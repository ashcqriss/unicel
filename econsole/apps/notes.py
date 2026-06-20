"""Notes app: quick notes with an inline reader."""

from __future__ import annotations

import curses
from typing import Any

from ..widgets import InputField, truncate, wrap_text
from .base import AppPane


class NotesApp(AppPane):
    app_name = "notes"
    app_label = "Notes"

    def __init__(self, pane_id: int = 0, context: Any = None):
        super().__init__(pane_id, context)
        self.mode = "list"  # list | view | input
        self.field = InputField(prompt="title: ")

    @property
    def _store(self):
        return getattr(self.context, "notes", None) if self.context else None

    def header_title(self, focused: bool) -> str:
        n = len(self._store.all()) if self._store else 0
        return f"Notes ({n})"

    def status_hint(self) -> str:
        if self.mode == "input":
            return "Enter=save · Esc=cancel"
        if self.mode == "view":
            return "Esc=back"
        return "↑↓ select · Enter=read · a=add · d=delete"

    def handle_key(self, key: int) -> bool:
        store = self._store
        if store is None:
            return False
        notes = store.all()
        if self.mode == "input":
            action = self.field.handle_key(key)
            if action and action[0] == "submit":
                title = action[1].strip()
                if title:
                    store.add(title)
                self.field.clear()
                self.mode = "list"
            elif action and action[0] == "cancel":
                self.field.clear()
                self.mode = "list"
            return True
        if self.mode == "view":
            if key in (27, ord("q")):
                self.mode = "list"
            return True
        # list mode
        if key in (curses.KEY_UP, ord("k")):
            self.move_selection(-1, len(notes))
        elif key in (curses.KEY_DOWN, ord("j")):
            self.move_selection(1, len(notes))
        elif key in (curses.KEY_ENTER, 10, 13):
            if notes:
                self.mode = "view"
        elif key == ord("a"):
            self.mode = "input"
            self.field.clear()
        elif key == ord("d"):
            if notes:
                store.remove(notes[self.selected]["id"])
                self.clamp_selection(len(store.all()))
        else:
            return False
        return True

    def render_body(self, surface, focused: bool) -> None:
        store = self._store
        if store is None:
            surface.text(0, 0, "notes store unavailable", role="error")
            return
        notes = store.all()
        self.clamp_selection(len(notes))

        if self.mode == "input":
            surface.text(0, 0, "New note", role="accent")
            self.field.render(surface, 2, focused=True)
            return

        if self.mode == "view" and notes:
            note = notes[self.selected]
            surface.text(0, 0, truncate(note["title"], surface.width), role="accent")
            surface.text(1, 0, note.get("updated", "")[:19], role="dim")
            surface.hline(2)
            body = note.get("body") or "(no body — quick note)"
            for i, line in enumerate(wrap_text(body, surface.width)):
                if 3 + i >= surface.height:
                    break
                surface.text(3 + i, 0, line, role="text")
            return

        if not notes:
            surface.text(0, 0, "No notes yet. Press 'a' to add one.", role="dim")
            return
        start, end = self.visible_window(len(notes), surface.height)
        for row, idx in enumerate(range(start, end)):
            note = notes[idx]
            selected = idx == self.selected
            prefix = "▸ " if selected else "  "
            line = f"{prefix}{truncate(note['title'], surface.width - 2)}"
            surface.text(row, 0, line, role="selection" if (selected and focused) else "text")
