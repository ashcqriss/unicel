"""User Manager app: the local user register (maximum three users)."""

from __future__ import annotations

import curses
from typing import Any

from ..stores import UserStore
from ..widgets import InputField, truncate
from .base import AppPane


class UserManagerApp(AppPane):
    app_name = "users"
    app_label = "User Manager"

    def __init__(self, pane_id: int = 0, context: Any = None):
        super().__init__(pane_id, context)
        self.mode = "list"
        self.field = InputField(prompt="name: ")
        self.message = ""

    @property
    def _store(self):
        return getattr(self.context, "users", None) if self.context else None

    def header_title(self, focused: bool) -> str:
        n = len(self._store.all()) if self._store else 0
        return f"User Manager ({n}/{UserStore.MAX_USERS})"

    def status_hint(self) -> str:
        if self.mode == "input":
            return "Enter=create · Esc=cancel"
        return "↑↓ select · Enter=set current · a=add · d=delete"

    def handle_key(self, key: int) -> bool:
        store = self._store
        if store is None:
            return False
        users = store.all()
        if self.mode == "input":
            action = self.field.handle_key(key)
            if action and action[0] == "submit":
                try:
                    store.add(action[1])
                    self.message = ""
                except ValueError as exc:
                    self.message = str(exc)
                self.field.clear()
                self.mode = "list"
            elif action and action[0] == "cancel":
                self.field.clear()
                self.mode = "list"
            return True
        if key in (curses.KEY_UP, ord("k")):
            self.move_selection(-1, len(users))
        elif key in (curses.KEY_DOWN, ord("j")):
            self.move_selection(1, len(users))
        elif key in (curses.KEY_ENTER, 10, 13):
            if users:
                self._set_current(users[self.selected])
        elif key == ord("a"):
            if len(users) >= UserStore.MAX_USERS:
                self.message = f"maximum of {UserStore.MAX_USERS} users reached"
            else:
                self.mode = "input"
                self.field.clear()
                self.message = ""
        elif key == ord("d"):
            if users:
                store.remove(users[self.selected]["id"])
                self.clamp_selection(len(store.all()))
        else:
            return False
        return True

    def _set_current(self, user: dict) -> None:
        if not self.context:
            return
        self.context.config.set("current_user", user["name"])
        if user.get("theme"):
            self.context.set_theme(user["theme"])
        if user.get("profile"):
            self.context.set_profile(user["profile"])
        self.message = f"active user: {user['name']}"

    def render_body(self, surface, focused: bool) -> None:
        store = self._store
        if store is None:
            surface.text(0, 0, "user store unavailable", role="error")
            return
        users = store.all()
        self.clamp_selection(len(users))
        if self.mode == "input":
            surface.text(0, 0, "Create user", role="accent")
            self.field.render(surface, 2, focused=True)
            if self.message:
                surface.text(4, 0, self.message, role="error")
            return

        current = self.context.config.get("current_user") if self.context else None
        if not users:
            surface.text(0, 0, "No users yet. Press 'a' to add (max 3).", role="dim")
        for i, user in enumerate(users):
            if i >= surface.height - 1:
                break
            selected = i == self.selected
            is_current = user["name"] == current
            avatar = (user.get("avatar") or user["name"][:1]).upper()[:2]
            star = "★" if is_current else " "
            theme = user.get("theme") or "default"
            prefix = "▸" if selected else " "
            line = f"{prefix}{star} ({avatar}) {truncate(user['name'], 18):<18} theme:{theme}"
            surface.text(i, 0, truncate(line, surface.width),
                         role="selection" if (selected and focused) else "text")
        if self.message:
            surface.text(surface.height - 1, 0, truncate(self.message, surface.width), role="ok")
