"""The single-layer pane manager.

This implements the window model described in the spec: panes are *tiled*, never
stacked. The states from the spec map onto manager state as follows:

==================  =========================================================
Spec state          Manager representation
==================  =========================================================
Full screen         ``zoom`` is on (focused pane fills the work area), or a
                    single visible pane.
Split screen        Two or more visible panes tiled along ``orientation``.
Partial screen      A single visible pane while others are hidden, or a pane
                    rendered with profile margins (E-Ink/AR).
Hidden pane         ``Pane.state == HIDDEN`` — not drawn, restorable.
Small tab           Every pane (especially hidden ones, and UNISHELL) appears
                    in the tab strip; UNISHELL keeps its upper-left tab.
==================  =========================================================
"""

from __future__ import annotations

from typing import Any, Optional

from ..geometry import Rect
from .base import Pane


class PaneManager:
    def __init__(self) -> None:
        self.panes: list[Pane] = []
        self.focused_id: Optional[int] = None
        self.orientation: str = "h"  # 'h' = side by side, 'v' = stacked
        self.zoom: bool = False
        self._next_id: int = 1
        #: Last computed geometry; useful for hit-testing and tests.
        self.geometry: dict[int, Rect] = {}

    # --- identity --------------------------------------------------------
    def allocate_id(self) -> int:
        pid = self._next_id
        self._next_id += 1
        return pid

    def get(self, pane_id: int) -> Optional[Pane]:
        for pane in self.panes:
            if pane.id == pane_id:
                return pane
        return None

    def index_of(self, pane_id: int) -> int:
        for i, pane in enumerate(self.panes):
            if pane.id == pane_id:
                return i
        return -1

    # --- adding / removing ----------------------------------------------
    def add(self, pane: Pane, context: Any = None, focus: bool = True) -> Pane:
        if pane.id is None or pane.id <= 0:
            pane.id = self.allocate_id()
        else:
            self._next_id = max(self._next_id, pane.id + 1)
        pane.context = context
        self.panes.append(pane)
        if focus or self.focused_id is None:
            self.focus(pane.id)
        return pane

    def remove(self, pane_id: int) -> bool:
        pane = self.get(pane_id)
        if pane is None or not pane.on_close():
            return False
        idx = self.index_of(pane_id)
        self.panes.remove(pane)
        if self.focused_id == pane_id:
            self.zoom = False
            self._focus_neighbour(idx)
        return True

    def _focus_neighbour(self, removed_index: int) -> None:
        visible = self.visible_panes()
        if not visible:
            # Keep focus on any remaining pane (e.g. a hidden UNISHELL).
            self.focused_id = self.panes[0].id if self.panes else None
            return
        target = min(removed_index, len(visible) - 1)
        self.focus(visible[target].id)

    # --- focus -----------------------------------------------------------
    def focused(self) -> Optional[Pane]:
        return self.get(self.focused_id) if self.focused_id is not None else None

    def focus(self, pane_id: int) -> bool:
        pane = self.get(pane_id)
        if pane is None:
            return False
        if pane.state == Pane.HIDDEN:
            pane.state = Pane.VISIBLE  # focusing a hidden pane reveals it
        previous = self.focused()
        if previous is not None and previous.id != pane_id:
            previous.on_blur()
        self.focused_id = pane_id
        pane.on_focus()
        return True

    def focus_next(self, step: int = 1) -> None:
        visible = self.visible_panes()
        if not visible:
            return
        ids = [p.id for p in visible]
        if self.focused_id in ids:
            i = (ids.index(self.focused_id) + step) % len(ids)
        else:
            i = 0
        self.focus(ids[i])

    def focus_index(self, n: int) -> bool:
        """Focus the pane whose position (1-based) among all panes is ``n``."""
        if 1 <= n <= len(self.panes):
            return self.focus(self.panes[n - 1].id)
        return False

    # --- visibility ------------------------------------------------------
    def visible_panes(self) -> list[Pane]:
        return [p for p in self.panes if p.state == Pane.VISIBLE]

    def hidden_panes(self) -> list[Pane]:
        return [p for p in self.panes if p.state == Pane.HIDDEN]

    def hide(self, pane_id: int) -> bool:
        pane = self.get(pane_id)
        if pane is None:
            return False
        pane.state = Pane.HIDDEN
        if self.focused_id == pane_id:
            self.zoom = False
            remaining = self.visible_panes()
            self.focused_id = remaining[0].id if remaining else pane_id
        return True

    def show(self, pane_id: int, focus: bool = True) -> bool:
        pane = self.get(pane_id)
        if pane is None:
            return False
        pane.state = Pane.VISIBLE
        if focus:
            self.focus(pane_id)
        return True

    def toggle_hidden(self, pane_id: int) -> bool:
        pane = self.get(pane_id)
        if pane is None:
            return False
        return self.hide(pane_id) if pane.state == Pane.VISIBLE else self.show(pane_id)

    # --- layout controls -------------------------------------------------
    def set_orientation(self, orientation: str) -> None:
        if orientation in ("h", "v"):
            self.orientation = orientation
            self.zoom = False

    def toggle_orientation(self) -> None:
        self.set_orientation("v" if self.orientation == "h" else "h")

    def toggle_zoom(self) -> None:
        self.zoom = not self.zoom

    SPLIT_DIRECTIONS = {
        "right": "h", "left": "h", "up": "v", "down": "v",
        "horizontal": "h", "vertical": "v",
    }

    def split(self, new_pane: Pane, direction: str, context: Any = None) -> Pane:
        """Add ``new_pane`` next to the focused pane in ``direction``."""
        orientation = self.SPLIT_DIRECTIONS.get(direction, "h")
        self.set_orientation(orientation)
        focused_index = self.index_of(self.focused_id) if self.focused_id else len(self.panes)
        new_pane.context = context
        if new_pane.id is None or new_pane.id <= 0:
            new_pane.id = self.allocate_id()
        insert_at = focused_index + 1 if direction in ("right", "down", "horizontal", "vertical") else focused_index
        insert_at = max(0, min(insert_at, len(self.panes)))
        self.panes.insert(insert_at, new_pane)
        self.focus(new_pane.id)
        return new_pane

    # --- resizing --------------------------------------------------------
    def resize_focused(self, delta: float) -> None:
        """Grow (delta>0) or shrink (delta<0) the focused pane's weight."""
        pane = self.focused()
        if pane is None:
            return
        pane.weight = max(0.2, min(8.0, pane.weight + delta))

    def equalize(self) -> None:
        for pane in self.panes:
            pane.weight = 1.0

    # --- geometry --------------------------------------------------------
    def layout(self, area: Rect) -> dict[int, Rect]:
        """Compute the rectangle for each visible pane within ``area``."""
        visible = self.visible_panes()
        result: dict[int, Rect] = {}
        if not visible:
            self.geometry = result
            return result

        if self.zoom:
            focused = self.focused()
            if focused is None or focused.state == Pane.HIDDEN:
                focused = visible[0]
            result[focused.id] = area
            self.geometry = result
            return result

        weights = [max(0.2, p.weight) for p in visible]
        rects = (area.split_h(weights) if self.orientation == "h"
                 else area.split_v(weights))
        for pane, rect in zip(visible, rects):
            result[pane.id] = rect
        self.geometry = result
        return result

    def pane_at(self, y: int, x: int) -> Optional[Pane]:
        for pane_id, rect in self.geometry.items():
            if rect.contains(y, x):
                return self.get(pane_id)
        return None
