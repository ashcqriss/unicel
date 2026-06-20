"""Easter eggs for UNISHELL — the fun, hidden corner of E-Console.

Each helper returns a list of ``(text, role)`` lines so the shell can print them
in colour via ``ctx.shell_print``. Kept curses-free and deterministic enough to
unit-test (``fortune``/``sudo`` randomness aside).

The eggs are intentionally discoverable with the ``eggs`` command — friendly,
like ``man fortune``, rather than truly secret.
"""

from __future__ import annotations

import random
import textwrap

Line = tuple[str, str]

# Catalogue shown by the `eggs` command and documented in docs/EASTER-EGGS.md.
EGGS: list[tuple[str, str]] = [
    ("neofetch / fetch", "System info + E-Console logo (configurable via 'neofetch config')"),
    ("sl", "A steam locomotive chuffs by when you fat-finger 'ls'"),
    ("cowsay <text>", "An ASCII cow says whatever you tell it"),
    ("fortune", "A random terminal/E-Ink fortune"),
    ("coffee / tea", "HTTP 418 — the shell is, regrettably, a teapot"),
    ("xyzzy", "A nod to Colossal Cave Adventure"),
    ("sudo <cmd>", "Permission theatrics (try 'sudo make me a sandwich')"),
    ("matrix", "Wake up, Neo… also flips you to the green theme"),
    ("theme apply rainbow", "Unlocks the secret 🌈 theme (hidden from 'theme list')"),
    ("calc 6*7", "A few numbers have opinions about themselves"),
    ("Konami code", "↑ ↑ ↓ ↓ ← → ← → B A in the browser preview"),
]


def eggs_list() -> list[Line]:
    out: list[Line] = [("🥚 E-Console easter eggs:", "accent"), ("", "text")]
    for trigger, desc in EGGS:
        out.append((f"  {trigger:<22} {desc}", "text"))
    out.append(("", "text"))
    out.append(("…and a couple I'm not telling you about. 😉", "dim"))
    return out


def train() -> list[Line]:
    art = [
        "      ====        ________                ___________",
        "  _D _|  |_______/        \\__I_I_____===__|_________|",
        "   |(_)---  |   H\\________/ |   |        =|___ ___|  ",
        "   /     |  |   H  |  |     |   |         ||_| |_||  ",
        "  |      |  |   H  |__--------------------| [___] |  ",
        "  | ________|___H__/__|_____/[][]~\\_______|       |  ",
        "  |/ |   |-----------I_____I [][] []  D   |=======|__",
        "__/ =| o |=-~~\\  /~~\\  /~~\\  /~~\\ ____Y___________|__",
        " |/-=|___|=   O=====O=====O=====O|_____/~\\___/      ",
        "  \\_/      \\__/  \\__/  \\__/  \\__/      \\_/           ",
    ]
    lines: list[Line] = [(row, "warn") for row in art]
    lines.append(("", "text"))
    lines.append(("🚂  you typed `sl` — did you mean `ls`?  choo choo!", "dim"))
    return lines


def cowsay(text: str) -> list[Line]:
    text = (text or "E-Console says moo!").strip()
    wrapped = textwrap.wrap(text, 38) or [""]
    width = max(len(w) for w in wrapped)
    out: list[Line] = [(" " + "_" * (width + 2), "accent2")]
    if len(wrapped) == 1:
        out.append((f"< {wrapped[0]} >", "accent2"))
    else:
        for i, w in enumerate(wrapped):
            left = "/" if i == 0 else ("\\" if i == len(wrapped) - 1 else "|")
            right = "\\" if i == 0 else ("/" if i == len(wrapped) - 1 else "|")
            out.append((f"{left} {w.ljust(width)} {right}", "accent2"))
    out.append((" " + "-" * (width + 2), "accent2"))
    out += [
        ("        \\   ^__^", "text"),
        ("         \\  (oo)\\_______", "text"),
        ("            (__)\\       )\\/\\", "text"),
        ("                ||----w |", "text"),
        ("                ||     ||", "text"),
    ]
    return out


_FORTUNES = [
    "The best UI is the one that's already on screen.",
    "A pane in the hand is worth two in the stack.",
    "E-Ink: where pixels go to think before they move.",
    "There are only two hard things: cache invalidation, naming panes, and off-by-one errors.",
    "rm -rf / your doubts.",
    "Real hackers count refreshes per minute, not frames per second.",
    "UNISHELL remembers. UNISHELL is patient. UNISHELL is the shell.",
    "Keyboard-first, because your mouse hand needs the coffee.",
    "A watched progress bar never completes.",
    "The terminal is mightier than the GUI.",
    "Low power, high focus.",
    "When in doubt, split the pane.",
]


def fortune() -> list[Line]:
    return [("🔮 " + random.choice(_FORTUNES), "text")]


def teapot() -> list[Line]:
    return [
        ("            ;,'", "accent"),
        ("    _o_    ;:;'", "accent"),
        (" ,-.'---`.__ ;", "accent"),
        ("((j`=====',-'", "accent"),
        (" `-\\     /", "accent"),
        ("    `-=-'", "accent"),
        ("", "text"),
        ("HTTP 418 — I'm a teapot. ☕ Short and stout.", "warn"),
    ]


_SUDO_DENIALS = [
    "This incident will be reported. 🚨",
    "Nice try.",
    "You shall not pass. 🧙",
    "With great power comes great responsibility — request denied.",
]


def sudo(argv: list[str]) -> list[Line]:
    joined = " ".join(argv).strip().lower()
    if joined == "make me a sandwich":
        return [("Okay.", "ok")]
    if not joined:
        return [("usage: sudo <command>  (spoiler: it won't help here)", "dim")]
    return [(random.choice(_SUDO_DENIALS), "error")]


def matrix() -> list[Line]:
    return [
        ("Wake up, Neo…", "ok"),
        ("The Matrix has you…", "ok"),
        ("Follow the white rabbit. 🐇", "ok"),
        ("", "text"),
        ("(theme → matrix)", "dim"),
    ]


def xyzzy() -> list[Line]:
    return [("Nothing happens.", "dim")]


def calc_flavor(value: float) -> str | None:
    """Return a cheeky suffix for certain calculator results."""
    try:
        if float(value) == 42:
            return "✨ the Answer to Life, the Universe, and Everything"
        if float(value) == 1337:
            return "😎 l33t"
        if float(value) == 69:
            return "nice."
    except (TypeError, ValueError):
        return None
    return None
