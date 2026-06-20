"""Neofetch app: a colourful, side-by-side fetch with a live config view.

Two views toggled with ``o``/Tab:
  - "fetch"  — logo beside the info table, with the classic colour-block row.
  - "config" — adjust the logo, the colour blocks, and which fields show; every
               change is saved to the ``neofetch`` config section immediately.
"""

from __future__ import annotations

import curses
from typing import Any

from .. import neofetch
from ..widgets import truncate
from .base import AppPane

_LOGO_CHOICES = ["auto"] + neofetch.LOGO_NAMES


class NeofetchApp(AppPane):
    app_name = "neofetch"
    app_label = "neofetch"

    def __init__(self, pane_id: int = 0, context: Any = None):
        super().__init__(pane_id, context)
        self.view = "fetch"
        self.cfg = neofetch.config_for(context)

    def header_title(self, focused: bool) -> str:
        return "neofetch" + ("" if self.view == "fetch" else " · config")

    def status_hint(self) -> str:
        if self.view == "fetch":
            return "o = configure · refreshes live"
        return "↑↓ select · space toggle · ←→ logo · r reset · o = preview"

    # --- options model ---------------------------------------------------
    def _options(self) -> list[dict]:
        opts = [
            {"kind": "logo", "label": "Logo", "value": self.cfg.get("logo", "auto")},
            {"kind": "blocks", "label": "Colour blocks",
             "value": "on" if self.cfg.get("color_blocks", True) else "off"},
        ]
        disabled = set(self.cfg.get("disabled", []))
        for key, label in neofetch.ALL_FIELDS:
            opts.append({"kind": "field", "key": key, "label": label,
                         "value": key not in disabled})
        return opts

    def _save(self) -> None:
        neofetch.save_config(self.context, self.cfg)

    def handle_key(self, key: int) -> bool:
        if key in (ord("o"), ord("\t"), 9):
            self.view = "config" if self.view == "fetch" else "fetch"
            return True
        if self.view != "config":
            return False
        opts = self._options()
        if key in (curses.KEY_UP, ord("k")):
            self.move_selection(-1, len(opts))
        elif key in (curses.KEY_DOWN, ord("j")):
            self.move_selection(1, len(opts))
        elif key == ord("r"):
            self.cfg = {"logo": "auto", "color_blocks": True,
                        "disabled": list(neofetch.DEFAULT_DISABLED)}
            self._save()
        elif key in (ord(" "), curses.KEY_ENTER, 10, 13, curses.KEY_LEFT, curses.KEY_RIGHT):
            self._activate(opts[self.selected], key)
        else:
            return False
        return True

    def _activate(self, opt: dict, key: int) -> None:
        if opt["kind"] == "logo":
            step = -1 if key == curses.KEY_LEFT else 1
            i = (_LOGO_CHOICES.index(self.cfg.get("logo", "auto")) + step) % len(_LOGO_CHOICES)
            self.cfg["logo"] = _LOGO_CHOICES[i]
        elif opt["kind"] == "blocks":
            self.cfg["color_blocks"] = not self.cfg.get("color_blocks", True)
        elif opt["kind"] == "field":
            disabled = set(self.cfg.get("disabled", []))
            disabled.symmetric_difference_update({opt["key"]})
            self.cfg["disabled"] = list(disabled)
        self._save()

    # --- rendering -------------------------------------------------------
    def render_body(self, surface, focused: bool) -> None:
        if self.view == "config":
            self._render_config(surface, focused)
        else:
            self._render_fetch(surface)

    def _render_fetch(self, surface) -> None:
        logo = neofetch.pick_logo(self.cfg, self.context)
        info = neofetch.gather(self.context, self.cfg)
        logo_w = max((len(row) for row in logo), default=0)
        for i, row in enumerate(logo):
            surface.text(i, 0, row, role="accent")

        right = logo_w + 3
        title = neofetch.title_line(self.context)
        surface.text(0, right, title, role="accent")
        surface.text(1, right, "─" * len(title), role="dim")
        label_w = max((len(label) for label, _ in info), default=0)
        row = 2
        for label, value in info:
            if row >= surface.height:
                break
            surface.text(row, right, label + ":", role="accent")
            surface.text(row, right + label_w + 2, truncate(value, surface.width - right - label_w - 2),
                         role="text")
            row += 1

        if self.cfg.get("color_blocks", True):
            y = max(len(logo), row) + 1
            if y < surface.height:
                col = 0
                for idx in neofetch.COLOR_BLOCK_INDICES:
                    surface.raw(y, col, "██", surface.colors.color_attr(idx))
                    col += 2
            if y + 1 < surface.height:
                col = 0
                for idx in neofetch.COLOR_BLOCK_INDICES:
                    surface.raw(y + 1, col, "██", surface.colors.color_attr(idx, bold=True))
                    col += 2

    def _render_config(self, surface, focused: bool) -> None:
        opts = self._options()
        self.clamp_selection(len(opts))
        surface.text(0, 0, "Adjust neofetch — changes save automatically", role="dim")
        start, end = self.visible_window(len(opts), surface.height - 1)
        for i, idx in enumerate(range(start, end)):
            opt = opts[idx]
            selected = idx == self.selected
            if opt["kind"] == "field":
                mark = "[x]" if opt["value"] else "[ ]"
                text = f"{mark} {opt['label']}"
            else:
                arrows = " ‹ › " if opt["kind"] == "logo" else " "
                text = f"{opt['label']}:{arrows}{opt['value']}"
            prefix = "▸ " if selected else "  "
            surface.text(1 + i, 0, prefix + text,
                         role="selection" if (selected and focused) else "text")
