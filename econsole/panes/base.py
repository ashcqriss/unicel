"""Base class for every pane in the single-layer window model.

A pane is a rectangular region that can be focused and receives key input when
focused. Panes never overlap; the :class:`~econsole.panes.manager.PaneManager`
assigns each visible pane a rectangle that tiles the work area.
"""

from __future__ import annotations

from typing import Any


class Pane:
    VISIBLE = "visible"
    HIDDEN = "hidden"

    #: Panes that should never be destroyed (UNISHELL). Set on the subclass.
    persistent = False

    def __init__(self, pane_id: int, kind: str, title: str):
        self.id = pane_id
        self.kind = kind
        self.title = title
        self.state = Pane.VISIBLE
        self.weight = 1.0
        #: Injected by the manager: the shared shell context (config, stores,
        #: command registry, notifications, ...).
        self.context: Any = None

    # --- lifecycle hooks -------------------------------------------------
    def on_focus(self) -> None:
        """Called when this pane gains focus."""

    def on_blur(self) -> None:
        """Called when this pane loses focus."""

    def on_close(self) -> bool:
        """Return ``True`` to allow closing, ``False`` to veto."""
        return not self.persistent

    # --- rendering / input ----------------------------------------------
    def render(self, surface, focused: bool) -> None:  # pragma: no cover - curses
        """Draw the pane into ``surface``. Override in subclasses."""

    def handle_key(self, key: int) -> bool:
        """Handle a key. Return ``True`` if consumed, ``False`` to bubble up."""
        return False

    # --- presentation helpers -------------------------------------------
    @property
    def tab_title(self) -> str:
        return self.title

    def status_hint(self) -> str:
        """Short hint shown in the status bar when this pane is focused."""
        return ""

    @property
    def is_visible(self) -> bool:
        return self.state == Pane.VISIBLE
