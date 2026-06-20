# Building the E-Console OS image

Roadmap steps **1 (Debian minimal image)**, **2 (boot into E-Console)** and
**17 (bootable Pi / x86_64 image)** are OS-integration work. They can't be
produced or validated inside a plain container, so this repo ships them as
reviewed scaffolding to run on a real Debian build host.

> ⚠️ These steps need root and a build host. Read the scripts before running.

## 1. Minimal Debian rootfs

Use `mmdebstrap` (lighter and rootless-friendly vs `debootstrap`) to build a
**Debian Stable (bookworm)** minbase rootfs containing only the kernel, init,
Python, and the UNIX tools the spec requires (`vi/vim`, `git`, `ssh`, `tmux`,
`curl`, `wget`, `less`, `nano`, `python`, `apt`, plus `nftables`).

```sh
sudo ./packaging/build-image.sh x86_64     # Intel N100
sudo ./packaging/build-image.sh arm64      # Raspberry Pi 5 / CM5
```

The script copies `econsole/` to `/opt/econsole`, installs the session launcher
and systemd unit, creates the `user` account, and enables the service. Pick ARM
for battery/device prototypes and x86_64 for maximum Linux app compatibility, as
the spec recommends.

## 2. Boot directly into E-Console

Two supported approaches (the build script wires up the first):

**A. systemd unit on tty1** — `packaging/econsole.service` takes over `tty1`
(`Conflicts=getty@tty1`), logs in via PAM as `user`, and runs
`econsole-session`. The session script restarts E-Console on crash and drops to
a recovery shell after repeated failures (safe recovery mode).

**B. getty autologin** — keep `getty@tty1` but autologin `user`, then start the
shell from their profile:

```ini
# /etc/systemd/system/getty@tty1.service.d/autologin.conf
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin user --noclear %I $TERM
```

```sh
# ~user/.bash_profile  (only on the real console, never over SSH)
if [ "$(tty)" = "/dev/tty1" ]; then exec econsole-session; fi
```

### The `econsole` TERM type

The spec sets `TERM=econsole`. Until a custom terminfo entry is compiled and
installed (`/usr/share/terminfo`), `econsole-session.sh` automatically falls
back to `TERM=linux`, so nothing breaks on day one. A starter terminfo can alias
`econsole` to `linux` with the colour and box-drawing capabilities E-Console
relies on.

## 3. Pack into a bootable image (step 17)

Turn the rootfs into a flashable image:

- **x86_64:** add `grub-pc`/`systemd-boot`, create a GPT image with an ESP +
  ext4 root using `genimage` or `guestfish`, install the bootloader.
- **Raspberry Pi (arm64):** add the Pi firmware + `config.txt`/`cmdline.txt`,
  a FAT boot partition + ext4 root; flash with `bmaptool`/`dd`.

Build artifacts (`images/*.img`, `*.iso`) are git-ignored.

## 4. Immutable core + rollback (reliability goals)

For the "read-only core system / rollback snapshots / safe recovery" goals,
build the root as an **A/B** or **OverlayFS** system:

- Ship root read-only; mount a writable overlay for `/etc`, `/home`, and the
  XDG state E-Console writes (`~/.config/econsole`, `~/.local/share/econsole`).
- Use an **A/B partition** scheme (or `btrfs`/OverlayFS snapshots) so an update
  writes the inactive slot and a failed boot rolls back to the last-good slot.
- Keep a minimal **recovery** target that boots to a plain shell when the active
  slot fails (the session script already provides the last line of defence).

See `docs/SECURITY.md` for the firewall, permissions and update-channel design
that pair with this layout.
