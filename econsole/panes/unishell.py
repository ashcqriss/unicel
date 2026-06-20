"""UNISHELL: the permanent root shell pane.

UNISHELL is the primary system shell. Submitted lines are dispatched to the
E-Console command registry first; anything unrecognised falls through to the
system shell (``/bin/sh``), which is what makes the environment "terminal-first,
not terminal-only". It is marked persistent so the pane manager never destroys
it — when hidden it lives on as the small upper-left version tab.
"""

from __future__ import annotations

from typing import Any

from ..version import banner_version, tab_label
from .repl import ReplPane


class UnishellPane(ReplPane):
    persistent = True

    def __init__(self, pane_id: int = 1, context: Any = None):
        super().__init__(pane_id, kind="unishell", title="UNISHELL", prompt="▸ ", context=context)
        self._intro()

    def _intro(self) -> None:
        self.print(banner_version(), role="accent")
        self.print("the permanent root shell · single-layer panes", role="dim")
        self.print("type 'help' for commands · 'cmd cheatsheet' for everything · F1 for hotkeys",
                   role="dim")
        self.print("", role="text")

    def title_text(self) -> str:
        return tab_label()

    def status_hint(self) -> str:
        return "UNISHELL · type a command · ↑↓ history · PgUp/PgDn scroll"

    def run(self, text: str) -> None:
        self.print(f"▸ {text}", role="accent")
        if text.strip() == "clear":
            self.clear()
            return
        if self.context is None:
            self.print("(no shell context)", role="error")
            return
        result = self.context.run_command(text)
        if result.unknown:
            # Fall through to the system shell.
            code, output = self.context.run_system(text)
            if output:
                self.print(output.rstrip("\n"), role="text")
            if code not in (0, None):
                self.print(f"[exit {code}]", role="dim")
        elif result.message:
            self.print(result.message, role="ok" if result.ok else "error")
