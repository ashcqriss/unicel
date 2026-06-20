#!/usr/bin/env python3
"""Render E-Console to a plain-text grid — no real terminal required.

Used to generate the layout snapshots in the docs and to eyeball the UI without
booting curses. A ``GridWindow`` records every ``addnstr`` into a 2-D character
buffer, so calling ``app._render()`` paints into the grid exactly as it would on
screen (minus colour).

Usage:
    python tools/snapshot.py [scene] [--size WxH]

Scenes: default, activity, calendar, eink, ar, launcher
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class GridWindow:
    def __init__(self, height: int, width: int):
        self.h = height
        self.w = width
        self.grid = [[" "] * width for _ in range(height)]

    def getmaxyx(self):
        return (self.h, self.w)

    def addnstr(self, y, x, s, n=None, attr=0):
        if y < 0 or y >= self.h:
            return
        s = s if n is None else s[:n]
        for i, ch in enumerate(s):
            col = x + i
            if 0 <= col < self.w:
                self.grid[y][col] = ch

    addstr = addnstr

    def erase(self):
        self.grid = [[" "] * self.w for _ in range(self.h)]

    def refresh(self):
        pass

    def bkgd(self, *a, **k):
        pass

    def timeout(self, *a, **k):
        pass

    def render(self) -> str:
        return "\n".join("".join(row).rstrip() for row in self.grid)


def build_scene(scene: str, width: int, height: int) -> str:
    os.environ.setdefault("XDG_CONFIG_HOME", tempfile.mkdtemp())
    os.environ.setdefault("XDG_DATA_HOME", os.environ["XDG_CONFIG_HOME"])
    from econsole.app import EConsoleApp

    app = EConsoleApp()
    win = GridWindow(height, width)
    app.stdscr = win

    # Seed some data so the productivity panes aren't empty.
    app.activity.add("project", "E-Console OS")
    app.activity.add("task", "Implement pane manager")
    app.activity.add("habit", "Daily standup")
    app.notes.add("Design", "single-layer panes; no overlaps")

    if scene == "default":
        app.split_parabash("right")
        app.run_command("calc 42*17")
    elif scene == "activity":
        app.open_app("activity")
    elif scene == "calendar":
        app.open_app("calendar")
    elif scene == "launcher":
        app.open_launcher()
    elif scene == "eink":
        app.set_profile("eink")
        app.open_app("activity")
    elif scene == "ar":
        app.set_profile("ar")
        app.open_app("tasks")
    else:
        raise SystemExit(f"unknown scene: {scene}")

    app._render()
    return win.render()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("scene", nargs="?", default="default")
    parser.add_argument("--size", default="100x30")
    args = parser.parse_args(argv)
    width, height = (int(part) for part in args.size.lower().split("x"))
    print(build_scene(args.scene, width, height))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
