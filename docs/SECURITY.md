# Security & reliability design

The spec sets concrete reliability/security goals: a read-only core, rollback
snapshots, minimal background services, strict permissions, firewall-on by
default, separate app permissions, an automatic update channel, and a safe
recovery mode. This document maps each goal to a concrete mechanism — the parts
present in the shell today, and the parts the OS image layer adds.

## Firewall (enabled by default, default-deny inbound)

The **Firewall Panel** (`econsole/apps/firewall.py`) is a faithful, editable
*model*: a default policy (`INPUT DROP · OUTPUT ACCEPT · FORWARD DROP`) plus a
rule list (loopback, established, SSH in, HTTP/HTTPS + DNS out, drop the rest).
It persists to `~/.local/share/econsole/firewall.json` and is reflected in the
status bar (🛡).

On a real image, render this model to **`nftables`** at boot. Equivalent ruleset:

```nft
table inet econsole {
  chain input {
    type filter hook input priority 0; policy drop;
    iif "lo" accept
    ct state established,related accept
    tcp dport 22 accept            # SSH
    ip protocol icmp accept
  }
  chain forward { type filter hook forward priority 0; policy drop; }
  chain output { type filter hook output priority 0; policy accept; }
}
```

`packaging/build-image.sh` enables `nftables.service`. A follow-up generator
(`firewall.json → econsole.nft`) closes the loop between the panel and enforcement.

## Read-only core + rollback

- Root filesystem **read-only**; a writable overlay covers `/etc`, `/home` and
  E-Console's XDG state. All app data is already confined to XDG dirs and written
  **atomically** (`config._atomic_write`), so a power loss can't corrupt state.
- **A/B slots** (or OverlayFS/btrfs snapshots): updates write the inactive slot;
  a failed boot rolls back. See `docs/OS-IMAGE.md`.

## Minimal background services

Boot enables only what's needed: the kernel, `systemd`, `udev`, `nftables`, and
the E-Console UI on the console. No display manager, no compositor stack, no web
runtime — the UI is a single curses process.

## Strict / separated permissions

- E-Console runs as the unprivileged `user`, never root.
- The calculator uses an **AST-walking evaluator** (no `eval`, no name/attribute
  access) so a malicious expression can't reach the interpreter — see
  `econsole/calc.py` and its tests.
- Command handlers are sandboxed by the dispatcher: an exception becomes an error
  line, never a crash (`commands/registry.py`).
- Per-app permission profiles (network, filesystem scope) are a planned addition;
  on a systemd image they map naturally to per-app unit sandboxing
  (`ProtectSystem`, `PrivateNetwork`, `ReadOnlyPaths`).

## Automatic update channel

`auto_update` is a setting today (Settings app / `config.json`). On the image it
drives an A/B updater (`apt` from a pinned channel, or an image-based updater
such as RAUC/Mender) that stages to the inactive slot and reboots into it, with
automatic rollback on boot failure.

## Safe recovery mode

`packaging/econsole-session.sh` restarts E-Console on crash and, after repeated
fast failures, drops to a plain login shell instead of looping — so a bad update
or config never bricks the device. Pair with a recovery boot entry that targets
the last-good slot.

## Crash isolation in the shell

- Every command handler runs inside a try/except in the dispatcher.
- Every draw goes through `Surface`, which clips writes and swallows the
  bottom-right-cell `curses.error`.
- Stores fall back to defaults on corrupt/unreadable JSON rather than throwing.

These keep a single misbehaving app or command from taking down UNISHELL.
