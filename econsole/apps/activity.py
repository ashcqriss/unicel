"""Activity Handler: the unified productivity surface.

Combines tasks, habits, reminders, calendar events, goals and project states in
one list with a type filter, exactly as the spec describes.
"""

from __future__ import annotations

import curses
from typing import Any

from ..stores import ActivityStore
from ..widgets import InputField, truncate
from .base import AppPane

_FILTERS = ("all",) + ActivityStore.TYPES
_TYPE_TAG = {
    "task": "TASK", "habit": "HABT", "reminder": "RMND",
    "event": "EVNT", "goal": "GOAL", "project": "PROJ",
}
_STATUS_MARK = {"open": "○", "active": "◐", "done": "●"}


class ActivityApp(AppPane):
    app_name = "activity"
    app_label = "Activity Handler"

    def __init__(self, pane_id: int = 0, context: Any = None):
        super().__init__(pane_id, context)
        self.filter_index = 0
        self.mode = "list"
        self.field = InputField(prompt="new: ")

    @property
    def _store(self):
        return getattr(self.context, "activity", None) if self.context else None

    @property
    def _current_filter(self) -> str:
        return _FILTERS[self.filter_index]

    def _items(self) -> list[dict]:
        store = self._store
        if store is None:
            return []
        if self._current_filter == "all":
            return store.all()
        return store.by_type(self._current_filter)

    def header_title(self, focused: bool) -> str:
        return f"Activity Handler · filter: {self._current_filter}"

    def status_hint(self) -> str:
        if self.mode == "input":
            return "Enter=add · Esc=cancel"
        return "↑↓ select · Space=status · f=filter · a=add · d=delete"

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
                    item_type = self._current_filter if self._current_filter != "all" else "task"
                    store.add(item_type, title)
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
        elif key in (ord("f"), curses.KEY_RIGHT):
            self.filter_index = (self.filter_index + 1) % len(_FILTERS)
            self.selected = 0
        elif key == curses.KEY_LEFT:
            self.filter_index = (self.filter_index - 1) % len(_FILTERS)
            self.selected = 0
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
        store = self._store
        if store is None:
            surface.text(0, 0, "activity store unavailable", role="error")
            return
        items = self._items()
        self.clamp_selection(len(items))

        if self.mode == "input":
            surface.text(0, 0, f"New {self._current_filter if self._current_filter != 'all' else 'task'}",
                         role="accent")
            self.field.render(surface, 2, focused=True)
            return

        # summary line of counts
        counts = store.counts_by_type()
        summary = "  ".join(f"{_TYPE_TAG[t]}:{counts.get(t, 0)}" for t in ActivityStore.TYPES)
        surface.text(0, 0, truncate(summary, surface.width), role="dim")
        surface.hline(1)

        if not items:
            surface.text(2, 0, "Nothing here. Press 'a' to add, 'f' to change filter.", role="dim")
            return
        list_height = surface.height - 2
        start, end = self.visible_window(len(items), list_height)
        for row, idx in enumerate(range(start, end)):
            item = items[idx]
            selected = idx == self.selected
            mark = _STATUS_MARK.get(item.get("status", "open"), "○")
            tag = _TYPE_TAG.get(item.get("type", "task"), "TASK")
            due = f" ⏲ {item['due'][:10]}" if item.get("due") else ""
            prefix = "▸" if selected else " "
            line = f"{prefix}{mark} {tag} {truncate(item['title'], max(0, surface.width - 16))}{due}"
            role = "selection" if (selected and focused) else (
                "dim" if item.get("status") == "done" else "text")
            surface.text(2 + row, 0, truncate(line, surface.width), role=role)
