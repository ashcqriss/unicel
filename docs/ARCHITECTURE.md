# E-Console architecture

E-Console is a terminal-native desktop shell. This document explains how the
pieces fit so you can extend it (new app, new theme, new device profile) without
spelunking.

## Design goals (and how the code honours them)

| Principle            | Mechanism |
|----------------------|-----------|
| Terminal-first       | UNISHELL is the root pane; unknown commands fall through to `/bin/sh`. |
| Lightweight/low-power | Stdlib `curses` only — **zero runtime dependencies**. Tick-based redraw throttled per profile. |
| Single-layer windows | `PaneManager` tiles panes; there is no overlap/stacking code at all. |
| Keyboard-first       | A leader key + function keys; every action has a binding (`hotkeys.py`). |
| E-Ink / AR friendly  | `Profile` flags drive chrome density, ASCII vs Unicode borders, refresh cadence, FPS. |
| Small, testable core | Logic (geometry, calc, stores, manager) is curses-free and unit tested. |
| Crash isolation      | Command handlers and draws are wrapped so one failure can't take down the shell. |

## Layered module map

```
            ┌────────────────────────────────────────────┐
            │ app.py  EConsoleApp                          │  event loop · renderer
            │  - is the "shell context" passed everywhere  │  · input dispatch
            └───────────────┬──────────────────────────────┘
        ┌───────────────────┼───────────────────────────┐
        ▼                   ▼                           ▼
   panes/manager.py    commands/registry.py        apps/__init__.py
   single-layer model  dispatch + builtins         app registry
        │                   │                           │
        ▼                   ▼                           ▼
   panes/* (unishell,   commands/builtins.py        apps/* (calculator,
   parabash, repl,      (help, parabash, calc,      calendar, activity,
   launcher, base)      theme, firewall, …)         notes, settings, …)
        │                                               │
        └──────────────┬────────────────────────────────┘
                       ▼
   render.py (Surface) · theme.py (ColorManager) · profile.py
   geometry.py · widgets.py · config.py · stores.py · calc.py · hotkeys.py
```

### The "shell context"

`EConsoleApp` is constructed **without touching curses**, so it can be built in
tests and headless tools. It doubles as the *context* object handed to every
pane and command, exposing the verbs they need:

```
open_app(name, **kw)   open_launcher()      new_parabash([cmd])
split_parabash(dir)    close_pane(id)        run_command(line)
run_system(line)       set_theme(name)       set_profile(name)
quit()                 notify(msg)           .config .activity .notes .users
                                              .manager .registry .profile .theme
```

Panes and commands depend only on these methods (duck-typed), which keeps import
cycles out and makes the surface easy to mock.

## The pane model (`panes/manager.py`)

Panes are tiled, never stacked. State lives in three fields:

- per-pane `state` ∈ {`visible`, `hidden`} and a `weight` (size share),
- manager `orientation` ∈ {`h`, `v`},
- manager `zoom` (focused pane fills the work area).

`layout(area)` turns that into a `{pane_id: Rect}` map by calling
`Rect.split_h/split_v` with the visible panes' weights. The remainder of integer
division is added to the last cell, so panes **exactly tile** the area — no gaps,
no overlaps. UNISHELL is `persistent = True`, so `remove()` vetoes destroying it;
hiding it instead keeps it alive as the upper-left tab.

## Rendering (`render.py`)

Every pane draws through a `Surface`, never the raw window. The surface:

- clips all writes to the pane rectangle (panes use pane-relative coordinates),
- swallows the `curses.error` raised when writing the bottom-right cell — the
  single most common curses crash,
- resolves **semantic roles** (`text`, `accent`, `border_focus`, `status`, …) to
  attributes via the `ColorManager`, so panes never see colour pairs,
- picks Unicode or ASCII box-drawing characters based on the theme/profile.

The app loop does `erase → draw tabs → draw panes → draw status → refresh` on a
timer whose period is `profile.refresh_ms` (60 ms desktop, 400 ms E-Ink).

## Theming (`theme.py`)

Themes are **pure data** expressed against the 16-colour ANSI palette (8 base
colours + a "bright via bold" flag). That universality is deliberate: the same
theme renders on the Linux text console, E-Ink panels and xterm. `ColorManager`
allocates one colour pair per semantic role and degrades to monochrome
(reverse/bold/dim) when the terminal has no colour. Adding a theme is one
`_register(Theme(...))` call.

## Profiles (`profile.py`)

A `Profile` bundles device behaviour — `animations`, `show_borders`, `density`,
`grayscale`, `partial_refresh`, `refresh_ms`, `video_fps`, `default_theme`. The
renderer and panes read these flags instead of hard-coding device logic, so a
new device class is a new `Profile`.

## Data model (`stores.py`)

JSON documents under the XDG data dir, written atomically. The **Activity
Handler** is the single source of truth the spec asks for — Tasks and Calendar
are *views* over `ActivityStore` (filtered by type / by date) rather than
separate silos. `NotesStore` and `UserStore` (capped at 3) are independent.

## Extending

- **New app:** subclass `apps.base.AppPane`, implement `render_body` +
  `handle_key`, then `register(AppInfo(...))` in `apps/__init__.py`. It's
  instantly available via `app <name>`, the launcher, and (optionally) a command.
- **New command:** add a handler and `registry.add(...)` in `commands/builtins.py`.
- **New theme/profile:** one registration call in `theme.py` / `profile.py`.
- **New pane type:** subclass `panes.base.Pane` (or `panes.repl.ReplPane`).

## Known prototype limitations

- **Parabash** is a line-oriented command runner, not a full PTY terminal
  emulator, so full-screen TUIs (`vim`, `htop`) need the documented PTY upgrade.
- **Browser** is reader/text mode; the graphical `web --visual` pane is future.
- **Image/Media** render as ASCII/half-block and frame sequences, not decoded
  media.
- **Firewall Panel** is a faithful editable *model*; a real image renders it to
  `nftables` (see SECURITY.md).
