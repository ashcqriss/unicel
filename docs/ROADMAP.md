# Roadmap & status

The spec's suggested implementation order has 17 steps. Steps 3–16 (the shell
and apps) are implemented and runnable in this repo. Steps 1–2 and 17 are
OS-image work that is environment-specific — they are documented and scaffolded
here rather than built, because they can't be produced or validated inside a
plain container.

Legend: ✅ done · 🧩 scaffolded (scripts/docs, needs a build host) · 🔭 future

| # | Step | Status | Where |
|---|------|--------|-------|
| 1 | Debian minimal image | 🧩 | `docs/OS-IMAGE.md` |
| 2 | Boot directly into E-Console | 🧩 | `packaging/econsole.service`, `packaging/econsole-session.sh` |
| 3 | Implement UNISHELL | ✅ | `econsole/panes/unishell.py` |
| 4 | Implement pane manager | ✅ | `econsole/panes/manager.py` |
| 5 | Add Parabashes | ✅ | `econsole/panes/parabash.py` |
| 6 | Commands + hotkey system | ✅ | `econsole/commands/`, `econsole/hotkeys.py` |
| 7 | Settings / theme system | ✅ | `econsole/apps/settings.py`, `econsole/theme.py` |
| 8 | App launcher | ✅ | `econsole/panes/launcher.py` |
| 9 | Calendar / calculator / activity apps | ✅ | `econsole/apps/` |
| 10 | Image rendering | ✅ (ASCII; half-block via optional Pillow) | `econsole/apps/imagepane.py` |
| 11 | Browser text mode | ✅ | `econsole/apps/browser.py` |
| 12 | Visual browser pane | 🔭 | reader view today; graphical pane planned |
| 13 | E-Ink mode | ✅ | `econsole/profile.py` (`eink`), `eink-*` themes |
| 14 | AR / output profile | ✅ profile · 🔭 transport | `econsole/profile.py` (`ar`) |
| 15 | User manager | ✅ (max 3) | `econsole/apps/usermanager.py` |
| 16 | Firewall / security panel | ✅ model · 🧩 enforcement | `econsole/apps/firewall.py`, `docs/SECURITY.md` |
| 17 | Bootable image for Pi / x86_64 | 🧩 | `docs/OS-IMAGE.md` |

## Notable design choices

- **Stdlib-only core.** Zero runtime dependencies (Python `curses`). Runs
  identically on Raspberry Pi 5 / CM5 (ARM) and Intel N100 (x86_64). Pillow is an
  *optional* extra used only for richer image previews.
- **Single source of truth for the Activity Handler.** Tasks and Calendar are
  views over `ActivityStore`.
- **Universal 16-colour theming** so E-Ink, the Linux console and xterm all look
  right and monochrome degrades cleanly.

## Next increments (in priority order)

1. **Parabash PTY upgrade** — embed a real pseudo-terminal so `vim`/`htop` run
   inside a pane (needs a minimal terminal-emulation layer or `pyte`).
2. **Visual browser pane** (step 12) for the Desktop profile via an external
   renderer; keep the reader view as the default low-power path.
3. **AR transport** (step 14) — a thin output adapter that mirrors selected
   panes to a glasses companion (BLE/USB), driven by the existing `ar` profile.
4. **Firewall enforcement** — render the Firewall Panel model to `nftables` on a
   real image (see SECURITY.md).
5. **Image build automation** (steps 1, 2, 17) — wire `docs/OS-IMAGE.md` into a
   reproducible `debos`/`mmdebstrap` pipeline producing Pi + x86_64 images.
6. **Mouse support & pane drag-resize** for the Desktop profile.
