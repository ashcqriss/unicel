"""Media / Video viewer: low-FPS, frame-based output (the VideoPane).

The spec describes video as "low-FPS frame-based video output" — a deliberate
fit for E-Ink and AR targets. This pane advances through a sequence of text
frames at the profile's ``video_fps`` using the UI tick, rather than decoding a
real codec. Frames can be loaded from a directory of ``*.txt`` files (each file
is one frame); otherwise a built-in demo animation plays.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..widgets import truncate
from .base import AppPane

_DEMO_FRAMES = [
    "   ●        \n  E-CONSOLE \n   frame 1  \n  [>       ]",
    "    ●       \n  E-CONSOLE \n   frame 2  \n  [=>      ]",
    "     ●      \n  E-CONSOLE \n   frame 3  \n  [==>     ]",
    "      ●     \n  E-CONSOLE \n   frame 4  \n  [===>    ]",
    "       ●    \n  E-CONSOLE \n   frame 5  \n  [====>   ]",
    "        ●   \n  E-CONSOLE \n   frame 6  \n  [=====>  ]",
    "         ●  \n  E-CONSOLE \n   frame 7  \n  [======> ]",
    "          ● \n  E-CONSOLE \n   frame 8  \n  [=======>]",
]


class MediaApp(AppPane):
    app_name = "media"
    app_label = "Media Viewer"

    def __init__(self, pane_id: int = 0, context: Any = None, path: str | None = None):
        super().__init__(pane_id, context)
        self.frames = self._load(path) or _DEMO_FRAMES
        self.source = path or "demo animation"
        self.frame = 0
        self.playing = True
        self._tick = 0

    def _load(self, path: str | None) -> list[str] | None:
        if not path:
            return None
        p = Path(path).expanduser()
        try:
            if p.is_dir():
                files = sorted(p.glob("*.txt"))
                frames = [f.read_text(encoding="utf-8", errors="replace") for f in files]
                return frames or None
            if p.is_file():
                # A single file split on form-feed gives multi-frame clips.
                text = p.read_text(encoding="utf-8", errors="replace")
                return text.split("\f") or None
        except OSError:
            return None
        return None

    def header_title(self, focused: bool) -> str:
        return f"Media — {truncate(Path(self.source).name, 30)}"

    def status_hint(self) -> str:
        state = "playing" if self.playing else "paused"
        fps = self.context.profile.video_fps if self.context else 24
        return f"Space=play/pause · ←→ step · {state} · {fps} fps target"

    def _ticks_per_frame(self) -> int:
        profile = self.context.profile if self.context else None
        refresh_ms = profile.refresh_ms if profile else 60
        fps = max(1, profile.video_fps if profile else 24)
        frame_ms = 1000 / fps
        return max(1, round(frame_ms / max(1, refresh_ms)))

    def handle_key(self, key: int) -> bool:
        import curses
        if key == ord(" "):
            self.playing = not self.playing
        elif key in (curses.KEY_RIGHT, ord("l")):
            self.playing = False
            self.frame = (self.frame + 1) % len(self.frames)
        elif key in (curses.KEY_LEFT, ord("h")):
            self.playing = False
            self.frame = (self.frame - 1) % len(self.frames)
        else:
            return False
        return True

    def render_body(self, surface, focused: bool) -> None:
        # Advance the animation on the UI tick, throttled to the target fps.
        if self.playing and self.frames:
            self._tick += 1
            if self._tick % self._ticks_per_frame() == 0:
                self.frame = (self.frame + 1) % len(self.frames)

        if not self.frames:
            surface.text(0, 0, "no frames", role="dim")
            return
        frame_text = self.frames[self.frame % len(self.frames)]
        for i, line in enumerate(frame_text.split("\n")):
            if i >= surface.height - 1:
                break
            surface.text(i, 0, truncate(line, surface.width), role="text")
        footer = f"frame {self.frame + 1}/{len(self.frames)}  ({self.source})"
        surface.text(surface.height - 1, 0, truncate(footer, surface.width), role="dim")
