"""Headless render smoke test.

A stub curses window lets the entire draw path — tab strip, pane layout, status
bar and every app's ``render`` — run without a real terminal, so a typo in a
render method fails CI instead of only blowing up on a device.
"""

import curses
import unittest

from econsole import apps as app_registry
from econsole.app import EConsoleApp
from econsole.geometry import Rect
from econsole.hotkeys import LEADER
from econsole.panes.launcher import LauncherPane
from econsole.profile import PROFILES
from econsole.render import Surface
from econsole.theme import THEMES

from ._tmpenv import TempEnvTestCase

NAV_KEYS = [curses.KEY_DOWN, curses.KEY_UP, ord("j"), ord("k"), ord(" "),
            curses.KEY_NPAGE, curses.KEY_PPAGE, curses.KEY_LEFT, curses.KEY_RIGHT,
            ord("o")]  # 'o' toggles the neofetch config view


class StubWindow:
    """Minimal curses-window stand-in that records nothing and never errors."""

    def __init__(self, height=24, width=80):
        self.height = height
        self.width = width

    def getmaxyx(self):
        return (self.height, self.width)

    def addnstr(self, *args, **kwargs):
        return None

    def addstr(self, *args, **kwargs):
        return None

    def erase(self):
        return None

    def refresh(self):
        return None

    def bkgd(self, *args, **kwargs):
        return None

    def timeout(self, *args, **kwargs):
        return None


class RenderSmokeTest(TempEnvTestCase):
    def setUp(self):
        super().setUp()
        self.app = EConsoleApp()
        self.win = StubWindow()

    def _surface(self, theme=None, profile=None):
        rect = Rect(0, 0, 80, 22)
        return Surface(self.win, rect, self.app.colors,
                       theme or self.app.theme, profile or self.app.profile)

    def test_every_app_renders_and_handles_keys(self):
        for name in app_registry.APPS:
            pane = app_registry.create(name, context=self.app)
            self.assertIsNotNone(pane, f"factory for {name} returned None")
            for focused in (True, False):
                pane.render(self._surface(), focused)
            for key in NAV_KEYS:
                pane.handle_key(key)
            # Render again after input to catch state-dependent crashes.
            pane.render(self._surface(), True)

    def test_shell_panes_render(self):
        from econsole.panes.parabash import ParabashPane
        from econsole.panes.unishell import UnishellPane

        for pane in (UnishellPane(context=self.app),
                     ParabashPane(context=self.app, index=1),
                     LauncherPane(context=self.app)):
            for focused in (True, False):
                pane.render(self._surface(), focused)
            for key in NAV_KEYS:
                pane.handle_key(key)

    def test_renders_under_every_profile_and_theme(self):
        for profile in PROFILES.values():
            for theme in THEMES.values():
                surface = self._surface(theme=theme, profile=profile)
                self.app.manager.focused().render(surface, True)

    def test_app_full_render_path(self):
        # Drive the whole application render via the stub screen.
        self.app.stdscr = self.win
        self.app.new_parabash()
        self.app.open_app("activity")
        self.app._render()
        # Hidden pane + zoom + small-terminal paths.
        self.app.manager.hide(self.app.manager.panes[1].id)
        self.app.manager.toggle_zoom()
        self.app._render()
        self.app.stdscr = StubWindow(3, 10)  # too small
        self.app._render()

    def test_leader_keybindings(self):
        self.app.stdscr = self.win
        start = len(self.app.manager.panes)
        self.app._handle_key(LEADER)
        self.assertTrue(self.app._leader)
        self.app._handle_key(ord("n"))  # new parabash
        self.assertEqual(len(self.app.manager.panes), start + 1)
        for combo in ("z", "w", "o", "=", "h", "u"):
            self.app._handle_key(LEADER)
            self.app._handle_key(ord(combo))

    def test_function_keys(self):
        self.app.stdscr = self.win
        self.app._handle_key(curses.KEY_F2)  # launcher
        self.assertTrue(any(p.kind == "launcher" for p in self.app.manager.panes))
        self.app._handle_key(curses.KEY_F10)  # quit
        self.assertFalse(self.app.running)


if __name__ == "__main__":
    unittest.main()
