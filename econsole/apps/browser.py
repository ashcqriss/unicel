"""Text-mode Browser (the VisualBrowser's text counterpart).

Fetches a URL with the standard library and renders a readable text version.
The visual rendering pane (``web --visual``) is a future graphical pane; in the
terminal we provide the reader view, which is the primary, low-power path and
the only one available on E-Ink/AR profiles.
"""

from __future__ import annotations

import curses
import urllib.error
import urllib.request
from html.parser import HTMLParser
from typing import Any

from ..widgets import InputField, truncate, wrap_text
from .base import AppPane

_BLOCK_TAGS = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5",
               "h6", "section", "article", "header", "footer", "ul", "ol"}
_SKIP_TAGS = {"script", "style", "head", "noscript", "svg"}


class _Reader(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._skip += 1
        if tag == "title":
            self._in_title = True
        if tag in _BLOCK_TAGS:
            self.parts.append("\n")
        if tag == "li":
            self.parts.append("• ")

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS and self._skip:
            self._skip -= 1
        if tag == "title":
            self._in_title = False
        if tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._skip:
            return
        if self._in_title:
            self.title += data.strip() + " "
            return
        text = data.replace("\r", " ")
        if text.strip():
            self.parts.append(text)

    def text(self) -> str:
        raw = "".join(self.parts)
        lines = [ln.strip() for ln in raw.split("\n")]
        out: list[str] = []
        blank = False
        for line in lines:
            if not line:
                if not blank:
                    out.append("")
                blank = True
            else:
                out.append(line)
                blank = False
        return "\n".join(out).strip()


class BrowserApp(AppPane):
    app_name = "browser"
    app_label = "Browser"

    def __init__(self, pane_id: int = 0, context: Any = None, url: str | None = None):
        super().__init__(pane_id, context)
        self.url = url or ""
        self.field = InputField(self.url, prompt="url: ")
        self.mode = "input" if not url else "view"
        self.title_text = ""
        self.body = ""
        self.offset = 0
        self.status = "Enter a URL and press Enter."
        if url:
            self.fetch(url)

    def header_title(self, focused: bool) -> str:
        label = self.title_text or self.url or "Browser"
        return f"Browser — {truncate(label, 44)}"

    def status_hint(self) -> str:
        if self.mode == "input":
            return "Enter=go · Esc=cancel"
        return "g=address · ↑↓ scroll · PgUp/PgDn"

    def fetch(self, url: str) -> None:
        url = url.strip()
        if not url:
            return
        if "://" not in url:
            url = "https://" + url
        self.url = url
        self.offset = 0
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "E-Console/0.1 (text)"})
            with urllib.request.urlopen(request, timeout=8) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                raw = response.read(2_000_000)  # cap to 2MB
            html = raw.decode(charset, errors="replace")
            reader = _Reader()
            reader.feed(html)
            self.body = reader.text()
            self.title_text = reader.title.strip()
            self.status = f"loaded {url}"
        except (urllib.error.URLError, ValueError, OSError) as exc:
            self.body = ""
            self.title_text = ""
            self.status = f"error: {exc}"

    def handle_key(self, key: int) -> bool:
        if self.mode == "input":
            action = self.field.handle_key(key)
            if action and action[0] == "submit":
                self.mode = "view"
                self.fetch(action[1])
            elif action and action[0] == "cancel":
                self.mode = "view"
            return True
        if key in (ord("g"), ord("/")):
            self.mode = "input"
            self.field.set(self.url)
        elif key in (curses.KEY_UP, ord("k")):
            self.offset = max(0, self.offset - 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            self.offset += 1
        elif key == curses.KEY_NPAGE:
            self.offset += 10
        elif key == curses.KEY_PPAGE:
            self.offset = max(0, self.offset - 10)
        elif key in (curses.KEY_HOME, ord("g")):
            self.offset = 0
        else:
            return False
        return True

    def render_body(self, surface, focused: bool) -> None:
        if self.mode == "input":
            surface.text(0, 0, "Address", role="accent")
            self.field.render(surface, 1, focused=True)
            surface.text(3, 0, truncate(self.status, surface.width), role="dim")
            return
        lines = wrap_text(self.body, surface.width) if self.body else []
        if not lines:
            surface.text(0, 0, truncate(self.status, surface.width),
                         role="error" if self.status.startswith("error") else "dim")
            surface.text(2, 0, "Press 'g' to enter an address.", role="dim")
            return
        max_offset = max(0, len(lines) - (surface.height - 1))
        self.offset = min(self.offset, max_offset)
        view = lines[self.offset:self.offset + surface.height - 1]
        for i, line in enumerate(view):
            surface.text(i, 0, line, role="text")
        # footer
        pct = 100 if max_offset == 0 else int(100 * self.offset / max_offset)
        surface.text(surface.height - 1, 0,
                     truncate(f"{self.status}  [{pct}%]", surface.width), role="dim")
