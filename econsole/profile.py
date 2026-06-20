"""Display / device profiles.

A profile bundles the behavioural differences between device classes
(desktop, E-Ink reader, AR companion). The renderer and pane manager read
these flags rather than hard-coding per-device behaviour, so adding a new
device class is a matter of adding a :class:`Profile`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Profile:
    name: str
    label: str
    default_theme: str
    #: Whether decorative animations / transient redraws are allowed.
    animations: bool = True
    #: Draw pane borders. AR/E-Ink prefer minimal chrome.
    show_borders: bool = True
    #: 'normal' or 'compact' chrome density.
    density: str = "normal"
    #: Force high-contrast grayscale rendering (E-Ink panels).
    grayscale: bool = False
    #: Prefer partial-refresh redraws over full clears (E-Ink).
    partial_refresh: bool = False
    #: Event-loop tick in milliseconds. Larger = fewer redraws (good for E-Ink).
    refresh_ms: int = 80
    #: Target frames-per-second for the frame-based VideoPane.
    video_fps: int = 24
    #: Short description shown in Settings.
    description: str = ""


DESKTOP = Profile(
    name="desktop",
    label="Desktop",
    default_theme="econsole-dark",
    animations=True,
    show_borders=True,
    density="normal",
    grayscale=False,
    partial_refresh=False,
    refresh_ms=60,
    video_fps=24,
    description="Full keyboard/mouse, larger panes, browser/image/video support.",
)

EINK = Profile(
    name="eink",
    label="E-Ink",
    default_theme="eink-light",
    animations=False,
    show_borders=True,
    density="normal",
    grayscale=True,
    partial_refresh=True,
    refresh_ms=400,
    video_fps=2,
    description="High contrast, grayscale, reduced animation, partial-refresh, low-FPS.",
)

AR = Profile(
    name="ar",
    label="AR Companion",
    default_theme="ar-dark",
    animations=False,
    show_borders=False,
    density="compact",
    grayscale=False,
    partial_refresh=False,
    refresh_ms=120,
    video_fps=10,
    description="Compact floating panels, glanceable text, command-driven control.",
)

PROFILES: dict[str, Profile] = {p.name: p for p in (DESKTOP, EINK, AR)}


def get_profile(name: str) -> Profile:
    """Return the named profile, falling back to Desktop for unknown names."""
    return PROFILES.get(name, DESKTOP)
