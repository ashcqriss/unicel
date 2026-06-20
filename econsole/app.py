"""The E-Console application: event loop, renderer and shell context.

``EConsoleApp`` doubles as the *shell context* passed to panes and commands —
it exposes the verbs they need (``open_app``, ``new_parabash``, ``set_theme``,
``run_command``, ...). It is constructed without touching curses so it can be
built headlessly in tests; the curses session is entered only in :meth:`run`.
"""

from __future__ import annotations

import datetime as _dt
import os
import subprocess
from pathlib import Path
from typing import Any, Optional

from . import apps as app_registry
from .commands.builtins import register_builtins
from .commands.registry import CommandRegistry, CommandResult
from .config import Config
from .geometry import Rect
from .hotkeys import LEADER
from .panes.launcher import LauncherPane
from .panes.manager import PaneManager
from .panes.parabash import ParabashPane
from .panes.unishell import UnishellPane
from .profile import get_profile
from .render import Surface
from .stores import ActivityStore, NotesStore, UserStore
from .theme import THEMES, ColorManager, get_theme
from .version import tab_label
from .widgets import truncate


class EConsoleApp:
    def __init__(self, config_path: Path | None = None):
        self.config = Config(config_path)
        self.profile = get_profile(self.config.get("profile", "desktop"))
        self.theme = get_theme(self.config.get("theme", "econsole-dark"))
        self.colors = ColorManager()

        # Persistent stores (the Activity Handler is the shared model).
        self.activity = ActivityStore()
        self.notes = NotesStore()
        self.users = UserStore()

        # Command registry.
        self.registry = CommandRegistry()
        register_builtins(self.registry)

        # Pane manager + the permanent UNISHELL root pane.
        self.manager = PaneManager()
        self.manager.add(UnishellPane(pane_id=1, context=self), context=self)

        self.running = True
        self.stdscr = None
        self._leader = False
        self._notice = ""
        self._notice_ttl = 0

        if self.config.get("current_user") is None and self.users.all():
            self.config.set("current_user", self.users.all()[0]["name"])
        if self.config.get("first_run"):
            self.config.set("first_run", False)

    # ======================================================================
    # shell context API (used by panes and command handlers)
    # ======================================================================
    def notify(self, message: str, ttl: int = 12) -> None:
        self._notice = message
        self._notice_ttl = ttl

    def run_command(self, line: str) -> CommandResult:
        return self.registry.dispatch(self, line)

    def run_system(self, line: str) -> tuple[int, str]:
        line = line.strip()
        # Handle ``cd`` in-process so the shell's directory actually changes.
        if line == "cd" or line.startswith("cd "):
            target = line[2:].strip() or str(Path.home())
            try:
                os.chdir(os.path.expanduser(target))
                return (0, "")
            except OSError as exc:
                return (1, f"cd: {exc}")
        try:
            proc = subprocess.run(["/bin/sh", "-c", line], capture_output=True,
                                  text=True, timeout=30)
            return (proc.returncode, (proc.stdout or "") + (proc.stderr or ""))
        except subprocess.TimeoutExpired:
            return (124, "command timed out")
        except OSError as exc:
            return (1, str(exc))

    def set_theme(self, name: str) -> bool:
        if name not in THEMES:
            return False
        self.theme = get_theme(name)
        self.config.set("theme", name)
        self._apply_colors()
        self.notify(f"theme: {name}")
        return True

    def set_profile(self, name: str) -> bool:
        from .profile import PROFILES
        if name not in PROFILES:
            return False
        self.profile = get_profile(name)
        self.config.set("profile", name)
        # Adopt the profile's default theme so device switches look right.
        self.set_theme(self.profile.default_theme)
        if self.stdscr is not None:
            self.stdscr.timeout(self.profile.refresh_ms)
        self.notify(f"profile: {name}")
        return True

    def open_app(self, name: str, **kwargs):
        info = app_registry.resolve(name)
        if info is None:
            return None
        # Reuse an existing instance when no arguments are supplied.
        if not kwargs:
            for pane in self.manager.panes:
                if pane.kind == info.name:
                    self.manager.focus(pane.id)
                    return pane
        pane = app_registry.create(name, context=self, **kwargs)
        if pane is None:
            return None
        self.manager.add(pane, context=self)
        return pane

    def open_launcher(self):
        for pane in self.manager.panes:
            if pane.kind == "launcher":
                self.manager.focus(pane.id)
                return pane
        pane = LauncherPane(context=self)
        self.manager.add(pane, context=self)
        return pane

    def _parabash_index(self) -> int:
        return sum(1 for p in self.manager.panes if p.kind == "parabash") + 1

    def new_parabash(self, command: str | None = None):
        pane = ParabashPane(context=self, index=self._parabash_index(), command=command)
        self.manager.add(pane, context=self)
        return pane

    def split_parabash(self, direction: str):
        pane = ParabashPane(context=self, index=self._parabash_index())
        self.manager.split(pane, direction, context=self)
        return pane

    def close_pane(self, pane_id: int) -> bool:
        return self.manager.remove(pane_id)

    def quit(self) -> None:
        self.running = False

    # ======================================================================
    # curses lifecycle
    # ======================================================================
    def run(self) -> None:  # pragma: no cover - requires a terminal
        import curses
        curses.wrapper(self._main)

    def _apply_colors(self) -> None:
        self.colors.apply(self.theme)
        if self.stdscr is not None:
            self.stdscr.bkgd(" ", self.colors.attr("text"))

    def _main(self, stdscr) -> None:  # pragma: no cover - requires a terminal
        import curses
        self.stdscr = stdscr
        curses.curs_set(0)
        stdscr.keypad(True)
        stdscr.timeout(self.profile.refresh_ms)
        self.colors.start()
        self._apply_colors()
        while self.running:
            self._render()
            try:
                key = stdscr.getch()
            except KeyboardInterrupt:
                break
            if key == -1:
                if self._notice_ttl > 0:
                    self._notice_ttl -= 1
                continue
            self._handle_key(key)

    # ======================================================================
    # input
    # ======================================================================
    def _handle_key(self, key: int) -> None:
        import curses
        if self._leader:
            self._leader = False
            self._handle_leader(key)
            return
        if key == LEADER:
            self._leader = True
            self.notify("LEADER (Ctrl-A) — press a pane key", ttl=20)
            return
        if key == curses.KEY_RESIZE:
            return
        if key == curses.KEY_F1:
            self.open_app("cheatsheet")
            return
        if key == curses.KEY_F2:
            self.open_launcher()
            return
        if key == curses.KEY_F3:
            self.manager.focus_next()
            return
        if key == curses.KEY_F10:
            self.quit()
            return
        focused = self.manager.focused()
        if focused is not None:
            focused.handle_key(key)

    def _handle_leader(self, key: int) -> None:
        import curses
        manager = self.manager
        focused = manager.focused()
        if key in (ord("n"),):
            self.new_parabash()
        elif key in (ord("s"), ord("|")):
            self.split_parabash("right")
        elif key in (ord("v"), ord("-")):
            self.split_parabash("down")
        elif key == ord("w"):
            manager.toggle_orientation()
        elif key == ord("z"):
            manager.toggle_zoom()
        elif key == ord("h"):
            if focused:
                manager.hide(focused.id)
        elif key == ord("x"):
            if focused:
                self.close_pane(focused.id)
        elif key in (ord("o"), ord("\t"), 9):
            manager.focus_next()
        elif key == ord("u"):
            manager.focus(1)  # UNISHELL is always pane 1
        elif key == ord("q"):
            self.quit()
        elif key == ord("="):
            manager.equalize()
        elif key in (curses.KEY_RIGHT, curses.KEY_DOWN):
            manager.resize_focused(0.2)
        elif key in (curses.KEY_LEFT, curses.KEY_UP):
            manager.resize_focused(-0.2)
        elif key in (ord("?"),):
            self.open_app("cheatsheet")
        elif ord("1") <= key <= ord("9"):
            manager.focus(key - ord("0"))

    # ======================================================================
    # rendering
    # ======================================================================
    def _render(self) -> None:  # pragma: no cover - requires a terminal
        stdscr = self.stdscr
        stdscr.erase()
        maxy, maxx = stdscr.getmaxyx()
        if maxy < 4 or maxx < 24:
            try:
                stdscr.addnstr(0, 0, "terminal too small", maxx)
            except Exception:
                pass
            stdscr.refresh()
            return

        self._render_tabs(maxx)
        work = Rect(0, 1, maxx, maxy - 2)
        layout = self.manager.layout(work)
        focused_id = self.manager.focused_id
        for pane in self.manager.visible_panes():
            rect = layout.get(pane.id)
            if rect is None or rect.is_empty():
                continue
            surface = Surface(stdscr, rect, self.colors, self.theme, self.profile)
            pane.render(surface, focused=(pane.id == focused_id))
        self._render_status(maxy, maxx)
        stdscr.refresh()

    def _render_tabs(self, maxx: int) -> None:
        stdscr = self.stdscr
        # Background for the strip.
        try:
            stdscr.addnstr(0, 0, " " * maxx, maxx, self.colors.attr("tab"))
        except Exception:
            pass
        col = 0
        focused_id = self.manager.focused_id
        for pane in self.manager.panes:
            label = tab_label() if pane.kind == "unishell" else f"[{pane.id}] {pane.tab_title}"
            if pane.kind != "unishell":
                label = ("·" if not pane.is_visible else " ") + label
            label = f" {label} "
            role = "tab_active" if pane.id == focused_id else (
                "tab" if pane.is_visible else "dim")
            if col + len(label) > maxx:
                break
            try:
                stdscr.addnstr(0, col, label, len(label), self.colors.attr(role))
            except Exception:
                pass
            col += len(label)

    def _render_status(self, maxy: int, maxx: int) -> None:
        stdscr = self.stdscr
        row = maxy - 1
        try:
            stdscr.addnstr(row, 0, " " * maxx, maxx, self.colors.attr("status"))
        except Exception:
            pass
        focused = self.manager.focused()
        left = ""
        if self._leader:
            left = "LEADER ▸ n=new s=split z=zoom h=hide x=close o=next 1-9=focus q=quit"
        elif self._notice_ttl > 0 and self._notice:
            left = self._notice
        elif focused is not None:
            left = focused.status_hint()
        clock = _dt.datetime.now().strftime("%H:%M") if self.config.get("show_clock") else ""
        fw = "🛡" if self.config.get("firewall_enabled") else " "
        right = f"{fw} {self.profile.name}·{self.theme.name} {clock}".strip()
        try:
            stdscr.addnstr(row, 0, truncate(" " + left, maxx - len(right) - 1),
                           maxx - len(right) - 1, self.colors.attr("status"))
            stdscr.addnstr(row, max(0, maxx - len(right) - 1), right, len(right),
                           self.colors.attr("status"))
        except Exception:
            pass
        if self._notice_ttl > 0:
            self._notice_ttl -= 1


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point for ``python -m econsole`` and the ``econsole`` script."""
    import argparse

    parser = argparse.ArgumentParser(prog="econsole", description="E-Console terminal shell")
    parser.add_argument("--profile", help="start in a display profile (desktop/eink/ar)")
    parser.add_argument("--theme", help="start with a theme")
    parser.add_argument("--version", action="store_true", help="print version and exit")
    parser.add_argument("--self-test", action="store_true",
                        help="construct the shell headlessly and exit (no TTY needed)")
    args = parser.parse_args(argv)

    if args.version:
        from .version import banner_version
        print(banner_version())
        return 0

    app = EConsoleApp()
    if args.profile:
        app.set_profile(args.profile)
    if args.theme:
        app.set_theme(args.theme)

    if args.self_test:
        from .version import banner_version
        print(f"{banner_version()} — self-test OK")
        print(f"panes={len(app.manager.panes)} "
              f"commands={len(app.registry.all())} "
              f"apps={len(app_registry.APPS)} "
              f"themes={len(THEMES)}")
        return 0

    try:
        app.run()
    except KeyboardInterrupt:
        pass
    return 0
