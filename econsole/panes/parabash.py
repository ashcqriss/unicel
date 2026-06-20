"""Parabash: a secondary terminal pane.

A line-oriented system-shell pane with its own working directory and history.
It runs each submitted line through ``/bin/sh`` and shows the combined output.

Note: this is a command runner, not a full PTY terminal emulator — interactive,
full-screen programs (``vim``, ``htop``) need a real PTY, which is the documented
next step for Parabash. Day-to-day commands (``ls``, ``git``, ``cat``, ``python
script.py``) work as expected.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from .repl import ReplPane

#: Hard cap so a runaway command cannot freeze the UI.
COMMAND_TIMEOUT = 30


class ParabashPane(ReplPane):
    def __init__(self, pane_id: int = 0, context: Any = None, index: int = 1,
                 command: str | None = None):
        super().__init__(pane_id, kind="parabash", title=f"Parabash {index}",
                         prompt="$ ", context=context)
        self.index = index
        self.cwd = Path.home()
        self.print(f"Parabash {index} — system shell ({self.cwd})", role="dim")
        self.print("runs /bin/sh commands · 'cd' to navigate · Ctrl-L clears", role="dim")
        if command:
            self.run(command)

    def title_text(self) -> str:
        return f"Parabash {self.index} — {self.cwd.name or '/'}"

    def status_hint(self) -> str:
        return f"Parabash · {self.cwd} · runs /bin/sh · ↑↓ history"

    def _change_dir(self, target: str) -> None:
        dest = (self.cwd / target).expanduser() if not os.path.isabs(target) else Path(target)
        try:
            dest = dest.resolve()
            if dest.is_dir():
                self.cwd = dest
            else:
                self.print(f"cd: not a directory: {target}", role="error")
        except OSError as exc:
            self.print(f"cd: {exc}", role="error")

    def run(self, text: str) -> None:
        self.print(f"$ {text}", role="accent")
        stripped = text.strip()
        if stripped == "clear":
            self.clear()
            return
        if stripped == "cd" or stripped.startswith("cd "):
            target = stripped[2:].strip() or str(Path.home())
            self._change_dir(target)
            return
        try:
            proc = subprocess.run(
                ["/bin/sh", "-c", text],
                cwd=str(self.cwd),
                capture_output=True,
                text=True,
                timeout=COMMAND_TIMEOUT,
            )
            output = (proc.stdout or "") + (proc.stderr or "")
            if output.strip():
                self.print(output.rstrip("\n"), role="text")
            if proc.returncode != 0:
                self.print(f"[exit {proc.returncode}]", role="dim")
        except subprocess.TimeoutExpired:
            self.print(f"[timed out after {COMMAND_TIMEOUT}s]", role="error")
        except OSError as exc:
            self.print(f"error: {exc}", role="error")
