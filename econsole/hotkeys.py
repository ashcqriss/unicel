"""Global hotkey definitions.

E-Console is keyboard-first. Pane management uses a tmux-style *leader* key
(Ctrl-A) so the bindings work no matter which pane has focus and never collide
with the text a pane is receiving. Function keys provide direct shortcuts for
the most common actions.

This module is the single source of truth: the event loop dispatches against
:data:`LEADER` and the constants here, and the Cheatsheet app renders
:data:`HOTKEYS` directly, so the documentation can never drift from behaviour.
"""

from __future__ import annotations

# Leader key: Ctrl-A.
LEADER = 0x01
LEADER_LABEL = "Ctrl-A"


class Key:
    """Named hotkey entry for the cheatsheet."""

    def __init__(self, combo: str, description: str, category: str = "Panes"):
        self.combo = combo
        self.description = description
        self.category = category


# Order here is the order shown in the cheatsheet.
HOTKEYS: list[Key] = [
    Key(f"{LEADER_LABEL} then n", "New Parabash pane", "Panes"),
    Key(f"{LEADER_LABEL} then s", "Split right (side by side)", "Panes"),
    Key(f"{LEADER_LABEL} then v", "Split down (stacked)", "Panes"),
    Key(f"{LEADER_LABEL} then w", "Toggle split orientation", "Panes"),
    Key(f"{LEADER_LABEL} then z", "Toggle full-screen (zoom) pane", "Panes"),
    Key(f"{LEADER_LABEL} then h", "Hide focused pane (to tab)", "Panes"),
    Key(f"{LEADER_LABEL} then x", "Close focused pane", "Panes"),
    Key(f"{LEADER_LABEL} then o", "Focus next pane", "Panes"),
    Key(f"{LEADER_LABEL} then 1..9", "Focus pane by number", "Panes"),
    Key(f"{LEADER_LABEL} then ←/→/↑/↓", "Resize focused pane", "Panes"),
    Key(f"{LEADER_LABEL} then =", "Equalize pane sizes", "Panes"),
    Key(f"{LEADER_LABEL} then u", "Focus UNISHELL", "Panes"),
    Key(f"{LEADER_LABEL} then q", "Quit E-Console", "System"),
    Key("F1", "Open Hotkey Cheatsheet", "System"),
    Key("F2", "Open App Launcher", "System"),
    Key("F3", "Focus next pane", "System"),
    Key("F10", "Quit E-Console", "System"),
    Key("Tab / ↑↓", "Navigate within a pane", "Navigation"),
    Key("Enter", "Activate / submit", "Navigation"),
    Key("Esc", "Cancel / back", "Navigation"),
]


def by_category() -> dict[str, list[Key]]:
    out: dict[str, list[Key]] = {}
    for key in HOTKEYS:
        out.setdefault(key.category, []).append(key)
    return out
