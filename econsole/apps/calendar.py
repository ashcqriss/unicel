"""Calendar app: a month grid with activity markers.

The grid is a view over the Activity Handler — any dated item (event, reminder,
due task, ...) marks its day, and the selected day's items are listed below.
"""

from __future__ import annotations

import calendar as _calendar
import curses
import datetime as _dt
from typing import Any

from ..widgets import truncate
from .base import AppPane

_WEEK = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
_MONTHS = ["", "January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"]


class CalendarApp(AppPane):
    app_name = "calendar"
    app_label = "Calendar"

    def __init__(self, pane_id: int = 0, context: Any = None, date: _dt.date | None = None):
        super().__init__(pane_id, context)
        self.cursor = date or _dt.date.today()
        self._cal = _calendar.Calendar(firstweekday=0)  # Monday

    def header_title(self, focused: bool) -> str:
        return f"Calendar — {_MONTHS[self.cursor.month]} {self.cursor.year}"

    def status_hint(self) -> str:
        return "←→ day · ↑↓ week · [ ] month · t=today"

    def _shift(self, days: int) -> None:
        self.cursor += _dt.timedelta(days=days)

    def _shift_month(self, delta: int) -> None:
        month = self.cursor.month - 1 + delta
        year = self.cursor.year + month // 12
        month = month % 12 + 1
        day = min(self.cursor.day, _calendar.monthrange(year, month)[1])
        self.cursor = _dt.date(year, month, day)

    def handle_key(self, key: int) -> bool:
        if key in (curses.KEY_LEFT, ord("h")):
            self._shift(-1)
        elif key in (curses.KEY_RIGHT, ord("l")):
            self._shift(1)
        elif key in (curses.KEY_UP, ord("k")):
            self._shift(-7)
        elif key in (curses.KEY_DOWN, ord("j")):
            self._shift(7)
        elif key in (ord("["), curses.KEY_PPAGE):
            self._shift_month(-1)
        elif key in (ord("]"), curses.KEY_NPAGE):
            self._shift_month(1)
        elif key in (ord("t"), ord("T")):
            self.cursor = _dt.date.today()
        else:
            return False
        return True

    def _has_activity(self, day: _dt.date) -> bool:
        if not self.context or not getattr(self.context, "activity", None):
            return False
        return bool(self.context.activity.for_date(day.isoformat()))

    def render_body(self, surface, focused: bool) -> None:
        today = _dt.date.today()
        # Weekday header
        header = " ".join(f"{w:>3}" for w in _WEEK)
        surface.text(0, 0, header, role="accent")
        row = 1
        for week in self._cal.monthdatescalendar(self.cursor.year, self.cursor.month):
            col = 0
            for day in week:
                cell = f"{day.day:>3}"
                role = "text"
                extra = 0
                if day.month != self.cursor.month:
                    role = "dim"
                if day == today:
                    role = "ok"
                if day == self.cursor:
                    role = "selection"
                    extra = curses.A_BOLD
                surface.text(row, col, cell, role=role, extra=extra)
                if self._has_activity(day):
                    surface.text(row, col + 3, "·", role="accent2")
                col += 4
            row += 1

        # Selected day's activity
        row += 1
        if row < surface.height:
            surface.hline(row - 1)
            label = self.cursor.strftime("%A %d %b %Y")
            surface.text(row, 0, label, role="accent")
            row += 1
            items = []
            if self.context and getattr(self.context, "activity", None):
                items = self.context.activity.for_date(self.cursor.isoformat())
            if not items:
                surface.text(row, 0, "no activity — use: activity new \"…\"", role="dim")
            else:
                for item in items:
                    if row >= surface.height:
                        break
                    mark = "✓" if item.get("status") == "done" else "•"
                    line = f"{mark} [{item.get('type','')[:4]}] {item.get('title','')}"
                    surface.text(row, 0, truncate(line, surface.width), role="text")
                    row += 1
