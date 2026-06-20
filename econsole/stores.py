"""Persistent data stores for the productivity apps.

The Activity Handler is the unified model the spec calls for: it "combines
tasks, habits, reminders, calendar events, goals and project states". The Tasks
app and Calendar app are *views* over :class:`ActivityStore` rather than
separate data silos, which keeps a single source of truth.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any, Optional

from .config import JsonStore, data_dir


def _now_iso() -> str:
    return _dt.datetime.now().replace(microsecond=0).isoformat()


def _today_iso() -> str:
    return _dt.date.today().isoformat()


class _SeqStore(JsonStore):
    """A JsonStore holding ``{"seq": int, "items": [...]}``."""

    def __init__(self, path: Path):
        super().__init__(path, default={"seq": 0, "items": []})

    def _new_id(self) -> int:
        self.data["seq"] = int(self.data.get("seq", 0)) + 1
        return self.data["seq"]

    @property
    def items(self) -> list[dict[str, Any]]:
        return self.data.setdefault("items", [])

    def get(self, item_id: int) -> Optional[dict[str, Any]]:
        for item in self.items:
            if item.get("id") == item_id:
                return item
        return None

    def remove(self, item_id: int) -> bool:
        item = self.get(item_id)
        if item is None:
            return False
        self.items.remove(item)
        self.save()
        return True


class ActivityStore(_SeqStore):
    """Unified store of tasks, habits, reminders, events, goals and projects."""

    TYPES = ("task", "habit", "reminder", "event", "goal", "project")
    STATUS_CYCLE = ("open", "active", "done")

    def __init__(self, path: Path | None = None):
        super().__init__(path or (data_dir() / "activity.json"))

    def add(self, item_type: str, title: str, due: str | None = None,
            tags: list[str] | None = None, notes: str = "") -> dict[str, Any]:
        if item_type not in self.TYPES:
            item_type = "task"
        item = {
            "id": self._new_id(),
            "type": item_type,
            "title": title.strip(),
            "status": "open",
            "created": _now_iso(),
            "due": due,
            "tags": tags or [],
            "notes": notes,
        }
        self.items.append(item)
        self.save()
        return item

    def all(self) -> list[dict[str, Any]]:
        return list(self.items)

    def by_type(self, item_type: str) -> list[dict[str, Any]]:
        return [i for i in self.items if i.get("type") == item_type]

    def set_status(self, item_id: int, status: str) -> bool:
        item = self.get(item_id)
        if item is None:
            return False
        item["status"] = status
        if status == "done":
            item["completed"] = _now_iso()
        else:
            item.pop("completed", None)
        self.save()
        return True

    def cycle_status(self, item_id: int) -> bool:
        item = self.get(item_id)
        if item is None:
            return False
        cycle = self.STATUS_CYCLE
        current = item.get("status", "open")
        nxt = cycle[(cycle.index(current) + 1) % len(cycle)] if current in cycle else cycle[0]
        return self.set_status(item_id, nxt)

    def for_date(self, date_iso: str) -> list[dict[str, Any]]:
        return [i for i in self.items if (i.get("due") or "")[:10] == date_iso]

    def dated(self) -> list[dict[str, Any]]:
        return [i for i in self.items if i.get("due")]

    def upcoming(self, limit: int = 10) -> list[dict[str, Any]]:
        today = _today_iso()
        future = [i for i in self.dated() if (i["due"][:10] >= today) and i.get("status") != "done"]
        future.sort(key=lambda i: i["due"])
        return future[:limit]

    def counts_by_type(self) -> dict[str, int]:
        counts = {t: 0 for t in self.TYPES}
        for item in self.items:
            counts[item.get("type", "task")] = counts.get(item.get("type", "task"), 0) + 1
        return counts

    def open_count(self) -> int:
        return sum(1 for i in self.items if i.get("status") != "done")


class NotesStore(_SeqStore):
    def __init__(self, path: Path | None = None):
        super().__init__(path or (data_dir() / "notes.json"))

    def add(self, title: str, body: str = "") -> dict[str, Any]:
        note = {
            "id": self._new_id(),
            "title": title.strip() or "Untitled",
            "body": body,
            "created": _now_iso(),
            "updated": _now_iso(),
        }
        self.items.append(note)
        self.save()
        return note

    def update(self, note_id: int, title: str | None = None, body: str | None = None) -> bool:
        note = self.get(note_id)
        if note is None:
            return False
        if title is not None:
            note["title"] = title
        if body is not None:
            note["body"] = body
        note["updated"] = _now_iso()
        self.save()
        return True

    def all(self) -> list[dict[str, Any]]:
        return list(self.items)


class UserStore(_SeqStore):
    """Local user register, capped at three users per the spec."""

    MAX_USERS = 3

    def __init__(self, path: Path | None = None):
        super().__init__(path or (data_dir() / "users.json"))

    def add(self, name: str, avatar: str = "", theme: str | None = None,
            profile: str | None = None) -> dict[str, Any]:
        if len(self.items) >= self.MAX_USERS:
            raise ValueError(f"maximum of {self.MAX_USERS} users reached")
        name = name.strip()
        if not name:
            raise ValueError("user name cannot be empty")
        if any(u["name"].lower() == name.lower() for u in self.items):
            raise ValueError(f"user '{name}' already exists")
        user = {
            "id": self._new_id(),
            "name": name,
            "avatar": avatar or name[:1].upper(),
            "theme": theme,
            "profile": profile,
            "created": _now_iso(),
        }
        self.items.append(user)
        self.save()
        return user

    def all(self) -> list[dict[str, Any]]:
        return list(self.items)

    def by_name(self, name: str) -> Optional[dict[str, Any]]:
        for user in self.items:
            if user["name"].lower() == name.lower():
                return user
        return None
