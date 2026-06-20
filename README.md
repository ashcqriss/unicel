# E-Console OS

> A Debian/Linux-based, **terminal-first** operating environment.
> `UNISHELL` is the permanent root interface; the UI is a **single-layer pane
> model** (no overlapping windows) with built-in productivity apps and
> Desktop / E-Ink / AR display profiles.

This repository contains the **E-Console shell** — the heart of the project — as
a runnable, dependency-free Python/curses application, plus the scripts and
documentation for turning it into a bootable OS image.

```
UNISHELL v0.1.0
```

---

## What this is

E-Console is **not** a normal desktop and **not** a bare terminal. It is a
terminal-native desktop *shell*:

- **UNISHELL** is the permanent root shell. Even when hidden it stays as the
  small upper-left version tab.
- Panes are **tiled, never stacked**: `Full · Split · Partial · Hidden · Tab`.
- Built-in apps (Calendar, Calculator, Activity Handler, Notes, Tasks, Files,
  Settings, Firewall, …) open as panes, not floating windows.
- **Profiles** reshape the UI for the device: Desktop, E-Ink (grayscale,
  high-contrast, low-refresh), and AR companion (compact, glanceable).
- It stays **UNIX-compatible**: unknown commands fall through to `/bin/sh`, so
  `ls`, `git`, `python`, `ssh`, `vi` and friends work.

### The default layout (UNISHELL + a split Parabash)

```text
 UNISHELL v0.1.0   [2] Parabash 1
┌─────────────── UNISHELL v0.1.0 ────────────────┐┌────────────── Parabash 1 — root ───────────────┐
│UNISHELL v0.1.0                                 ││Parabash 1 — system shell (/root)               │
│the permanent root shell · single-layer panes   ││runs /bin/sh commands · 'cd' to navigate · Ctrl…│
│type 'help' for commands · 'cmd cheatsheet' for…││                                                │
│                                                ││                                                │
│ 42*17 = 714                                    ││                                                │
│▸                                               ││$                                               │
└────────────────────────────────────────────────┘└────────────────────────────────────────────────┘
 Parabash · /root · runs /bin/sh · ↑↓ history                         🛡 desktop·econsole-dark 09:29
```

### The Activity Handler (unified tasks/habits/reminders/events/goals/projects)

```text
┌──────── Activity Handler · filter: all ────────┐
│TASK:1  HABT:1  RMND:0  EVNT:0  GOAL:0  PROJ:1  │
│────────────────────────────────────────────────│
│▸○ PROJ E-Console OS                            │
│ ○ TASK Implement pane manager                  │
│ ○ HABT Daily standup                           │
└────────────────────────────────────────────────┘
 ↑↓ select · Space=status · f=filter · a=add · d=delete
```

Regenerate any of these with `python tools/snapshot.py <scene>` — no terminal
required (it renders into a text grid).

---

## Browser preview

[`index.html`](index.html) is a self-contained, interactive preview of the shell
— open it directly in a browser (or serve it via GitHub Pages). It mirrors the
real thing: the same 7 themes and 3 profiles, the single-layer pane model, and a
working UNISHELL command line. Try `help`, `calc 42*17`, `theme apply matrix`,
`profile set eink`, `parabash split right`, `activity new project "Ship v1"`.
No build step and no dependencies — it's one HTML file.

```sh
xdg-open index.html        # or just double-click it
python3 -m http.server     # then visit http://localhost:8000/
```

---

## Quick start

Requirements: **Python 3.9+** and a terminal. No third-party packages for the
core (stdlib `curses` only).

```sh
# Run from a clone (no install needed)
python3 -m econsole

# Or install the launcher
pip install -e .
econsole

# Start in a specific profile / theme
econsole --profile eink
econsole --theme matrix

# Headless checks (no TTY needed)
econsole --self-test
make test
```

On first launch you land in UNISHELL. Try:

```sh
help
calc 42*17
parabash split right
activity new project "OS Development"
theme apply eink-dark
profile set ar
firewall status
```

Press **F1** for the hotkey cheatsheet, **F2** for the app launcher.

---

## The single-layer window model

| Spec state    | In E-Console                                                        |
|---------------|--------------------------------------------------------------------|
| Full screen   | `zoom` on — focused pane fills the work area (leader → `z`)         |
| Split screen  | Two or more visible panes tiled along the split axis               |
| Partial       | A single visible pane while others are hidden (or profile margins) |
| Hidden pane   | Pane kept alive but undrawn; restorable from its tab               |
| Small tab     | Every pane shows in the top tab strip; UNISHELL keeps its tab      |

Resize, split, focus and hide are all keyboard-driven; see Hotkeys below.

---

## Hotkeys

Pane management uses a **leader key** (`Ctrl-A`, tmux-style) so it never clashes
with what a pane is receiving.

| Keys | Action |
|------|--------|
| `Ctrl-A` `n` | New Parabash pane |
| `Ctrl-A` `s` / `v` | Split right / split down |
| `Ctrl-A` `w` | Toggle split orientation |
| `Ctrl-A` `z` | Toggle full-screen (zoom) |
| `Ctrl-A` `h` / `x` | Hide / close focused pane |
| `Ctrl-A` `o` | Focus next pane |
| `Ctrl-A` `1`…`9` | Focus pane by number |
| `Ctrl-A` `←/→/↑/↓` | Resize focused pane |
| `Ctrl-A` `u` | Focus UNISHELL |
| `Ctrl-A` `q` / `F10` | Quit |
| `F1` / `F2` / `F3` | Cheatsheet / Launcher / Focus next |

---

## Commands (UNISHELL)

`help` lists everything; `cmd cheatsheet` opens the in-app reference. Highlights:

```sh
help · cmd cheatsheet · version · sysinfo · quit
parabash new|split <dir>|hide N|focus N   panes · focus N · hide N · zoom · split <dir>
calc <expr>            calendar [today]   activity [new [type] "…"]
tasks [new "…"]        notes [new "…"]    web [--visual] <url>
files [path]           image <path>       media [path]
app <name> · apps      settings           theme list|apply <name>
profile list|set <name>                   firewall [status|enable|disable]
users [add <name>|list]
```

Anything UNISHELL doesn't recognise is run through `/bin/sh` (with in-process
`cd`), so the environment stays a real working shell.

---

## Apps

Calculator · Calendar · **Activity Handler** (tasks/habits/reminders/events/
goals/projects) · Tasks · Notes · Settings · Theme Library · Hotkey Cheatsheet ·
User Manager (max 3) · Firewall Panel · File Manager · Browser (reader) · Image
Viewer · Media Viewer (low-FPS frames).

## Themes & profiles

- **Themes** (7): `econsole-dark`, `econsole-light`, `eink-dark`, `eink-light`,
  `ar-dark`, `matrix`, `amber`. Built on the universal 16-colour palette so they
  render on the Linux console, E-Ink panels and xterm alike, degrading to
  monochrome where there is no colour.
- **Profiles** (3): `desktop`, `eink` (grayscale, ASCII chrome, partial-refresh,
  low FPS), `ar` (compact, borderless, glanceable). Switching profiles adopts a
  fitting default theme and refresh cadence.

---

## Repository layout

```
econsole/            the shell (stdlib only)
  app.py             event loop + renderer + shell context
  geometry.py        Rect tiling math (headless-testable)
  render.py          Surface: clipped, theme-aware drawing
  theme.py           theme library + curses colour management
  profile.py         device profiles (desktop/eink/ar)
  config.py stores.py  XDG-backed JSON config + data stores
  calc.py            safe arithmetic evaluator (no eval)
  hotkeys.py widgets.py
  panes/             manager, base, repl, unishell, parabash, launcher
  commands/          registry + built-in commands
  apps/              all the app panes
tests/               70 unittest tests (run headless)
tools/snapshot.py    render the UI to text (docs/screenshots)
index.html           self-contained interactive browser preview
packaging/           systemd unit + session script for boot-to-shell
docs/                ARCHITECTURE · ROADMAP · OS-IMAGE · SECURITY
```

---

## Testing

```sh
make test        # 70 tests, ~0.05s, pure stdlib
make selftest    # headless construction summary
```

The geometry, calculator, stores, panes, themes and command layers are unit
tested, and a headless **render smoke test** drives every pane's draw path
(plus the full app render, leader keys and function keys) through a stub curses
window — so a typo in a render method fails CI instead of only on a device.

---

## From shell to OS image

Roadmap steps 3–16 (the shell and apps) are implemented and runnable here. The
OS-image steps (Debian minimal image, boot-directly-into-E-Console, read-only
root with rollback, bootable Pi/x86_64 images) are environment-specific and are
documented with scaffolding in **[docs/OS-IMAGE.md](docs/OS-IMAGE.md)** and
**[docs/SECURITY.md](docs/SECURITY.md)** rather than built here. See
**[docs/ROADMAP.md](docs/ROADMAP.md)** for the full status of all 17 steps and
**[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** for the design.

## License

MIT — see [LICENSE](LICENSE).
