"""Tasks app: a focused view of the Activity Handler's task items."""

from __future__ import annotations

import curses
from typing import Any

from ..widgets import InputField, truncate
from .base import AppPane

_CHECK = {"open": "[ ]", "active": "[~]", "done": "[x]"}


class TasksApp(AppPane):
    app_name = "tasks"
    app_label = "Tasks"
    item_type = "task"

    def __init__(self, pane_id: int = 0, context: Any = None):
        super().__init__(pane_id, context)
        self.mode = "list"
        self.field = InputField(prompt="task: ")

    @property
    def _store(self):
        return getattr(self.context, "activity", None) if self.context else None

    def _items(self) -> list[dict]:
        return self._store.by_type(self.item_type) if self._store else []

    def header_title(self, focused: bool) -> str:
        items = self._items()
        open_n = sum(1 for i in items if i.get("status") != "done")
        return f"{self.app_label} ({open_n}/{len(items)})"

    def status_hint(self) -> str:
        if self.mode == "input":
            return "Enter=add · Esc=cancel"
        return "↑↓ select · Space=cycle · a=add · d=delete"

    def handle_key(self, key: int) -> bool:
        store = self._store
        if store is None:
            return False
        items = self._items()
        if self.mode == "input":
            action = self.field.handle_key(key)
            if action and action[0] == "submit":
                title = action[1].strip()
                if title:
                    store.add(self.item_type, title)
                self.field.clear()
                self.mode = "list"
            elif action and action[0] == "cancel":
                self.field.clear()
                self.mode = "list"
            return True
        if key in (curses.KEY_UP, ord("k")):
            self.move_selection(-1, len(items))
        elif key in (curses.KEY_DOWN, ord("j")):
            self.move_selection(1, len(items))
        elif key in (ord(" "), curses.KEY_ENTER, 10, 13):
            if items:
                store.cycle_status(items[self.selected]["id"])
        elif key == ord("a"):
            self.mode = "input"
            self.field.clear()
        elif key == ord("d"):
            if items:
                store.remove(items[self.selected]["id"])
                self.clamp_selection(len(self._items()))
        else:
            return False
        return True

    def render_body(self, surface, focused: bool) -> None:
        if self._store is None:
            surface.text(0, 0, "activity store unavailable", role="error")
            return
        items = self._items()
        self.clamp_selection(len(items))
        if self.mode == "input":
            surface.text(0, 0, f"New {self.item_type}", role="accent")
            self.field.render(surface, 2, focused=True)
            return
        if not items:
            surface.text(0, 0, f"No {self.item_type}s yet. Press 'a' to add.", role="dim")
            return
        start, end = self.visible_window(len(items), surface.height)
        for row, idx in enumerate(range(start, end)):
            item = items[idx]
            selected = idx == self.selected
            status = item.get("status", "open")
            check = _CHECK.get(status, "[ ]")
            prefix = "▸" if selected else " "
            line = f"{prefix}{check} {truncate(item['title'], surface.width - 6)}"
            role = "selection" if (selected and focused) else ("dim" if status == "done" else "text")
            surface.text(row, 0, line, role=role)
