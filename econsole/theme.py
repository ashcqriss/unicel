"""Theme library and curses colour management.

Themes are expressed against the 16-colour ANSI palette (8 base colours plus a
"bright" flag rendered via bold). Sticking to the universal palette keeps the
shell readable on the Linux text console, E-Ink panels, ``xterm`` and AR
output alike, instead of relying on truecolour that many targets lack.

The :class:`Theme` data is pure data (no curses import) so the theme library is
importable and testable in a headless environment. The :class:`ColorManager`
is the only part that touches curses, and it imports it lazily.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Palette name -> (base ANSI index 0-7, bold?). Bold is used to reach the
# "bright" half of the 16-colour palette on 8-colour terminals.
PALETTE: dict[str, tuple[int, bool]] = {
    "black": (0, False),
    "red": (1, False),
    "green": (2, False),
    "yellow": (3, False),
    "blue": (4, False),
    "magenta": (5, False),
    "cyan": (6, False),
    "white": (7, False),
    "gray": (0, True),
    "grey": (0, True),
    "bright_red": (1, True),
    "bright_green": (2, True),
    "bright_yellow": (3, True),
    "bright_blue": (4, True),
    "bright_magenta": (5, True),
    "bright_cyan": (6, True),
    "bright_white": (7, True),
}

# Semantic roles that every theme provides. The renderer asks the ColorManager
# for an attribute by role name.
ROLES = (
    "text",
    "dim",
    "accent",
    "accent2",
    "border",
    "border_focus",
    "status",
    "tab",
    "tab_active",
    "selection",
    "ok",
    "warn",
    "error",
    "title",
)


@dataclass(frozen=True)
class Theme:
    name: str
    label: str
    profile_hint: str
    bg: str
    fg: str
    dim: str
    accent: str
    accent2: str
    border: str
    border_focus: str
    status_fg: str
    status_bg: str
    tab_fg: str
    tab_bg: str
    tab_active_fg: str
    tab_active_bg: str
    sel_fg: str
    sel_bg: str
    ok: str
    warn: str
    error: str
    high_contrast: bool = False
    description: str = ""
    #: Secret themes are appliable but hidden from `theme list` / Theme Library.
    hidden: bool = False

    def role_pairs(self) -> dict[str, tuple[str, str]]:
        """Map each semantic role to a concrete ``(fg, bg)`` palette pair."""
        return {
            "text": (self.fg, self.bg),
            "dim": (self.dim, self.bg),
            "accent": (self.accent, self.bg),
            "accent2": (self.accent2, self.bg),
            "title": (self.accent, self.bg),
            "border": (self.border, self.bg),
            "border_focus": (self.border_focus, self.bg),
            "status": (self.status_fg, self.status_bg),
            "tab": (self.tab_fg, self.tab_bg),
            "tab_active": (self.tab_active_fg, self.tab_active_bg),
            "selection": (self.sel_fg, self.sel_bg),
            "ok": (self.ok, self.bg),
            "warn": (self.warn, self.bg),
            "error": (self.error, self.bg),
        }


def _theme(**kwargs) -> Theme:
    return Theme(**kwargs)


THEMES: dict[str, Theme] = {}


def _register(theme: Theme) -> None:
    THEMES[theme.name] = theme


_register(_theme(
    name="econsole-dark", label="E-Console Dark", profile_hint="desktop",
    bg="black", fg="bright_white", dim="gray",
    accent="bright_cyan", accent2="bright_magenta",
    border="gray", border_focus="bright_cyan",
    status_fg="bright_white", status_bg="blue",
    tab_fg="gray", tab_bg="black",
    tab_active_fg="black", tab_active_bg="bright_cyan",
    sel_fg="black", sel_bg="bright_cyan",
    ok="bright_green", warn="bright_yellow", error="bright_red",
    description="Default desktop theme: dark background, cyan accents.",
))

_register(_theme(
    name="econsole-light", label="E-Console Light", profile_hint="desktop",
    bg="white", fg="black", dim="gray",
    accent="blue", accent2="magenta",
    border="gray", border_focus="blue",
    status_fg="white", status_bg="blue",
    tab_fg="gray", tab_bg="white",
    tab_active_fg="white", tab_active_bg="blue",
    sel_fg="white", sel_bg="blue",
    ok="green", warn="yellow", error="red",
    description="Light desktop theme for bright environments.",
))

_register(_theme(
    name="eink-dark", label="E-Ink Dark", profile_hint="eink",
    bg="black", fg="bright_white", dim="white",
    accent="bright_white", accent2="white",
    border="white", border_focus="bright_white",
    status_fg="black", status_bg="white",
    tab_fg="white", tab_bg="black",
    tab_active_fg="black", tab_active_bg="bright_white",
    sel_fg="black", sel_bg="bright_white",
    ok="bright_white", warn="bright_white", error="bright_white",
    high_contrast=True,
    description="High-contrast grayscale for inverted E-Ink panels.",
))

_register(_theme(
    name="eink-light", label="E-Ink Light", profile_hint="eink",
    bg="white", fg="black", dim="black",
    accent="black", accent2="black",
    border="black", border_focus="black",
    status_fg="white", status_bg="black",
    tab_fg="black", tab_bg="white",
    tab_active_fg="white", tab_active_bg="black",
    sel_fg="white", sel_bg="black",
    ok="black", warn="black", error="black",
    high_contrast=True,
    description="Paper-like high-contrast E-Ink theme (black on white).",
))

_register(_theme(
    name="ar-dark", label="AR Dark", profile_hint="ar",
    bg="black", fg="bright_white", dim="bright_cyan",
    accent="bright_cyan", accent2="bright_green",
    border="bright_cyan", border_focus="bright_white",
    status_fg="black", status_bg="bright_cyan",
    tab_fg="bright_cyan", tab_bg="black",
    tab_active_fg="black", tab_active_bg="bright_cyan",
    sel_fg="black", sel_bg="bright_cyan",
    ok="bright_green", warn="bright_yellow", error="bright_red",
    description="High-contrast compact theme for AR glass output.",
))

_register(_theme(
    name="matrix", label="Matrix", profile_hint="desktop",
    bg="black", fg="bright_green", dim="green",
    accent="bright_green", accent2="green",
    border="green", border_focus="bright_green",
    status_fg="black", status_bg="bright_green",
    tab_fg="green", tab_bg="black",
    tab_active_fg="black", tab_active_bg="bright_green",
    sel_fg="black", sel_bg="bright_green",
    ok="bright_green", warn="bright_yellow", error="bright_red",
    description="Green phosphor terminal aesthetic.",
))

_register(_theme(
    name="amber", label="Amber CRT", profile_hint="desktop",
    bg="black", fg="bright_yellow", dim="yellow",
    accent="bright_yellow", accent2="yellow",
    border="yellow", border_focus="bright_yellow",
    status_fg="black", status_bg="bright_yellow",
    tab_fg="yellow", tab_bg="black",
    tab_active_fg="black", tab_active_bg="bright_yellow",
    sel_fg="black", sel_bg="bright_yellow",
    ok="bright_green", warn="bright_yellow", error="bright_red",
    description="Warm amber monochrome CRT aesthetic.",
))


_register(_theme(
    name="rainbow", label="Rainbow", profile_hint="desktop",
    bg="black", fg="bright_white", dim="bright_blue",
    accent="bright_magenta", accent2="bright_cyan",
    border="bright_blue", border_focus="bright_yellow",
    status_fg="black", status_bg="bright_magenta",
    tab_fg="bright_cyan", tab_bg="black",
    tab_active_fg="black", tab_active_bg="bright_yellow",
    sel_fg="black", sel_bg="bright_green",
    ok="bright_green", warn="bright_yellow", error="bright_red",
    hidden=True,
    description="🌈 secret festive theme — try 'theme apply rainbow'.",
))


def get_theme(name: str) -> Theme:
    """Return the named theme, falling back to the default dark theme."""
    return THEMES.get(name, THEMES["econsole-dark"])


def list_themes(include_hidden: bool = False) -> list[Theme]:
    return [t for t in THEMES.values() if include_hidden or not t.hidden]


class ColorManager:
    """Translate theme roles into curses attributes.

    Allocates one curses colour pair per role and caches the resulting
    attribute (pair number OR'd with A_BOLD where the palette entry is bright).
    Degrades gracefully to monochrome attributes when the terminal lacks
    colour support.
    """

    #: Ad-hoc colour pairs (neofetch swatches) live above the role pairs.
    _COLOR_PAIR_BASE = 40

    def __init__(self) -> None:
        self._curses = None
        self._has_color = False
        self._attrs: dict[str, int] = {}
        self._next_pair = 1
        self._color_cache: dict[tuple[int, int], int] = {}
        self._color_next = self._COLOR_PAIR_BASE

    def start(self) -> None:
        import curses  # local import keeps the module headless-importable

        self._curses = curses
        try:
            curses.start_color()
            try:
                curses.use_default_colors()
            except curses.error:
                pass
            self._has_color = curses.has_colors()
        except curses.error:
            self._has_color = False

    def apply(self, theme: Theme) -> None:
        """(Re)build colour pairs for ``theme``. Safe to call on theme change."""
        curses = self._curses
        self._attrs = {}
        self._next_pair = 1
        self._color_cache = {}
        self._color_next = self._COLOR_PAIR_BASE
        if curses is None:
            return

        if not self._has_color:
            # Monochrome fallback: use reverse video to distinguish chrome.
            for role in ROLES:
                attr = curses.A_NORMAL
                if role in ("status", "tab_active", "selection"):
                    attr = curses.A_REVERSE
                elif role in ("dim",):
                    attr = curses.A_DIM
                elif role in ("accent", "title", "border_focus", "ok", "warn", "error"):
                    attr = curses.A_BOLD
                self._attrs[role] = attr
            return

        max_pairs = getattr(curses, "COLOR_PAIRS", 64) or 64
        for role, (fg_name, bg_name) in theme.role_pairs().items():
            fg_idx, fg_bold = PALETTE.get(fg_name, (7, False))
            bg_idx, _ = PALETTE.get(bg_name, (0, False))
            attr = curses.A_NORMAL
            if self._next_pair < max_pairs:
                try:
                    curses.init_pair(self._next_pair, fg_idx, bg_idx)
                    attr = curses.color_pair(self._next_pair)
                    self._next_pair += 1
                except curses.error:
                    attr = curses.A_NORMAL
            if fg_bold:
                attr |= curses.A_BOLD
            self._attrs[role] = attr

    def attr(self, role: str) -> int:
        """Return the curses attribute for a role (0 when headless)."""
        return self._attrs.get(role, 0)

    def color_attr(self, fg_index: int, bg_index: int = -1, bold: bool = False) -> int:
        """Return an attribute for a raw ANSI colour pair (e.g. neofetch swatches).

        Allocates and caches a colour pair on demand above the role-pair range.
        Falls back to bold/reverse video when the terminal has no colour.
        """
        curses = self._curses
        if curses is None:
            return 0
        if not self._has_color:
            return curses.A_REVERSE
        key = (fg_index, bg_index)
        if key not in self._color_cache:
            max_pairs = getattr(curses, "COLOR_PAIRS", 64) or 64
            attr = curses.A_NORMAL
            if self._color_next < max_pairs:
                try:
                    curses.init_pair(self._color_next, fg_index, bg_index)
                    attr = curses.color_pair(self._color_next)
                    self._color_next += 1
                except curses.error:
                    attr = curses.A_NORMAL
            self._color_cache[key] = attr
        attr = self._color_cache[key]
        return attr | curses.A_BOLD if bold else attr
