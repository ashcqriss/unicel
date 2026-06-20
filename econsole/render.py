"""Safe, theme-aware drawing surface.

Every pane draws through a :class:`Surface` rather than touching the curses
window directly. The surface clips all writes to the pane's rectangle and
swallows the ``curses.error`` raised when writing the bottom-right cell, which
removes the single most common class of curses crashes. It also resolves
semantic theme roles to attributes so panes never deal with colour pairs.

Coordinates passed to :class:`Surface` methods are *relative to the pane*, so a
pane can be drawn at any screen position without knowing where it lives.
"""

from __future__ import annotations

import curses

from .geometry import Rect

# Box-drawing character sets. ASCII is used for high-contrast/E-Ink targets and
# as a fallback for fonts without line-drawing glyphs.
BOX_UNICODE = {
    "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
    "h": "─", "v": "│", "tt": "┬", "bt": "┴", "lt": "├", "rt": "┤", "x": "┼",
}
BOX_ASCII = {
    "tl": "+", "tr": "+", "bl": "+", "br": "+",
    "h": "-", "v": "|", "tt": "+", "bt": "+", "lt": "+", "rt": "+", "x": "+",
}


class Surface:
    def __init__(self, win, rect: Rect, colors, theme, profile):
        self.win = win
        self.rect = rect
        self.colors = colors
        self.theme = theme
        self.profile = profile
        self.box_chars = BOX_ASCII if (theme.high_contrast or not profile.animations) else BOX_UNICODE

    @property
    def width(self) -> int:
        return self.rect.w

    @property
    def height(self) -> int:
        return self.rect.h

    def attr(self, role: str) -> int:
        return self.colors.attr(role)

    def text(self, row: int, col: int, s: str, role: str = "text", extra: int = 0,
             max_len: int | None = None) -> None:
        """Draw ``s`` at pane-relative ``(row, col)`` in a theme role, clipped."""
        self.raw(row, col, s, self.colors.attr(role) | extra, max_len)

    def raw(self, row: int, col: int, s: str, attr: int = 0,
            max_len: int | None = None) -> None:
        """Draw ``s`` with a raw curses attribute (used for neofetch swatches)."""
        if s is None or row < 0 or row >= self.rect.h:
            return
        s = str(s).replace("\t", "    ")
        if col < 0:
            s = s[-col:]
            col = 0
        avail = self.rect.w - col
        if avail <= 0:
            return
        if max_len is not None:
            avail = min(avail, max_len)
        s = s[:avail]
        if not s:
            return
        y = self.rect.y + row
        x = self.rect.x + col
        try:
            self.win.addnstr(y, x, s, len(s), attr)
        except curses.error:
            pass

    def fill(self, role: str = "text", ch: str = " ") -> None:
        attribute = self.colors.attr(role)
        line = ch * self.rect.w
        for r in range(self.rect.h):
            try:
                self.win.addnstr(self.rect.y + r, self.rect.x, line, self.rect.w, attribute)
            except curses.error:
                pass

    def hline(self, row: int, col: int = 0, length: int | None = None,
              ch: str | None = None, role: str = "border") -> None:
        if row < 0 or row >= self.rect.h:
            return
        ch = ch or self.box_chars["h"]
        length = self.rect.w - col if length is None else length
        self.text(row, col, ch * max(0, length), role=role)

    def box(self, role: str = "border", title: str | None = None,
            title_role: str = "title") -> None:
        """Draw a border around the pane edge with an optional centred title."""
        c = self.box_chars
        w, h = self.rect.w, self.rect.h
        if w < 2 or h < 2:
            return
        self.text(0, 0, c["tl"] + c["h"] * (w - 2) + c["tr"], role=role)
        for r in range(1, h - 1):
            self.text(r, 0, c["v"], role=role)
            self.text(r, w - 1, c["v"], role=role)
        self.text(h - 1, 0, c["bl"] + c["h"] * (w - 2) + c["br"], role=role)
        if title:
            label = f" {title} "
            if len(label) <= w - 2:
                self.text(0, max(1, (w - len(label)) // 2), label, role=title_role)

    def interior(self, margin: int = 1) -> "Surface":
        """Return a sub-surface inset by ``margin`` cells (inside a border)."""
        return Surface(self.win, self.rect.inset(margin, margin, margin, margin),
                       self.colors, self.theme, self.profile)
