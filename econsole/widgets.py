"""Small reusable TUI widgets and text helpers.

Kept dependency-free and (mostly) curses-free so the text utilities can be unit
tested. :class:`InputField` only references curses key constants, which are
plain integers available without a live terminal.
"""

from __future__ import annotations

import curses
from typing import Optional


def truncate(text: str, width: int, ellipsis: str = "…") -> str:
    text = str(text)
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width <= len(ellipsis):
        return text[:width]
    return text[: width - len(ellipsis)] + ellipsis


def wrap_text(text: str, width: int) -> list[str]:
    """Word-wrap ``text`` to ``width`` columns, preserving blank lines."""
    if width <= 0:
        return [text]
    out: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph:
            out.append("")
            continue
        line = ""
        for word in paragraph.split(" "):
            while len(word) > width:  # hard-break very long words
                if line:
                    out.append(line)
                    line = ""
                out.append(word[:width])
                word = word[width:]
            candidate = f"{line} {word}".strip()
            if len(candidate) <= width:
                line = candidate
            else:
                out.append(line)
                line = word
        out.append(line)
    return out


# Key constants resolved once. curses provides these as integers even headless.
KEY_BACKSPACE = {curses.KEY_BACKSPACE, 127, 8}
KEY_ENTER = {curses.KEY_ENTER, 10, 13}
KEY_ESCAPE = {27}


class InputField:
    """A single-line editable text field with a cursor.

    Returns a small action tuple from :meth:`handle_key` so the owning pane can
    react: ``("submit", text)``, ``("cancel", "")`` or ``("edit", text)``.
    """

    def __init__(self, text: str = "", prompt: str = ""):
        self.text = text
        self.prompt = prompt
        self.cursor = len(text)

    def clear(self) -> None:
        self.text = ""
        self.cursor = 0

    def set(self, text: str) -> None:
        self.text = text
        self.cursor = len(text)

    def handle_key(self, key: int) -> Optional[tuple[str, str]]:
        if key in KEY_ENTER:
            return ("submit", self.text)
        if key in KEY_ESCAPE:
            return ("cancel", "")
        if key in KEY_BACKSPACE:
            if self.cursor > 0:
                self.text = self.text[: self.cursor - 1] + self.text[self.cursor:]
                self.cursor -= 1
            return ("edit", self.text)
        if key == curses.KEY_DC:  # delete
            self.text = self.text[: self.cursor] + self.text[self.cursor + 1:]
            return ("edit", self.text)
        if key == curses.KEY_LEFT:
            self.cursor = max(0, self.cursor - 1)
            return ("edit", self.text)
        if key == curses.KEY_RIGHT:
            self.cursor = min(len(self.text), self.cursor + 1)
            return ("edit", self.text)
        if key == curses.KEY_HOME:
            self.cursor = 0
            return ("edit", self.text)
        if key == curses.KEY_END:
            self.cursor = len(self.text)
            return ("edit", self.text)
        if 32 <= key < 127:  # printable ASCII
            ch = chr(key)
            self.text = self.text[: self.cursor] + ch + self.text[self.cursor:]
            self.cursor += 1
            return ("edit", self.text)
        return None

    def render(self, surface, row: int, role: str = "text",
               prompt_role: str = "accent", focused: bool = True) -> None:
        col = 0
        if self.prompt:
            surface.text(row, 0, self.prompt, role=prompt_role)
            col = len(self.prompt)
        avail = max(0, surface.width - col)
        # Horizontal scroll so the cursor stays visible in a narrow field.
        start = max(0, self.cursor - avail + 1)
        visible = self.text[start:start + avail]
        surface.text(row, col, visible + " " * (avail - len(visible)), role=role)
        if focused:
            cursor_col = col + (self.cursor - start)
            ch = self.text[self.cursor] if self.cursor < len(self.text) else " "
            surface.text(row, cursor_col, ch, role=role, extra=curses.A_REVERSE)
