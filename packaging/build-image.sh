#!/bin/sh
# E-Console image build scaffold (roadmap steps 1 & 17).
#
# This is a TEMPLATE meant to run on a Debian build host with root/`mmdebstrap`,
# NOT inside this repo's CI container. It produces a minimal Debian rootfs that
# boots straight into E-Console. Review every step before running.
#
#   sudo ./packaging/build-image.sh x86_64   # or: arm64 (Pi 5 / CM5)
#
# Requires: mmdebstrap, and for disk images: guestfish or genimage + a kernel.

set -eu

ARCH="${1:-x86_64}"
SUITE="${SUITE:-bookworm}"          # Debian Stable
MIRROR="${MIRROR:-http://deb.debian.org/debian}"
ROOTFS="${ROOTFS:-./images/rootfs-$ARCH}"

case "$ARCH" in
    x86_64|amd64) DEB_ARCH=amd64 ;;
    arm64|aarch64) DEB_ARCH=arm64 ;;
    *) echo "unknown arch: $ARCH" >&2; exit 2 ;;
esac

command -v mmdebstrap >/dev/null || { echo "install mmdebstrap first" >&2; exit 1; }
mkdir -p "$(dirname "$ROOTFS")"

# Minimal package set: kernel, init, Python, and the UNIX tools the spec lists.
PACKAGES="linux-image-$DEB_ARCH,systemd-sysv,udev,python3,\
busybox,less,nano,vim,git,openssh-client,curl,wget,tmux,ca-certificates,\
nftables,console-setup,kbd"

echo ">> bootstrapping $SUITE/$DEB_ARCH into $ROOTFS"
mmdebstrap \
    --arch="$DEB_ARCH" \
    --variant=minbase \
    --include="$PACKAGES" \
    --customize-hook='mkdir -p "$1/opt/econsole"' \
    --customize-hook="copy-in ./econsole /opt/econsole/" \
    --customize-hook="copy-in ./packaging/econsole-session.sh /usr/local/bin/" \
    --customize-hook="copy-in ./packaging/econsole.service /etc/systemd/system/" \
    --customize-hook='chroot "$1" sh -c "
        useradd -m -s /bin/bash user || true;
        chmod +x /usr/local/bin/econsole-session.sh;
        ln -sf /usr/local/bin/econsole-session.sh /usr/local/bin/econsole-session;
        printf \"export PYTHONPATH=/opt\n\" > /etc/profile.d/econsole.sh;
        systemctl enable econsole.service;
        systemctl disable getty@tty1.service || true;
        systemctl enable nftables.service || true;
    "' \
    "$SUITE" "$ROOTFS" "$MIRROR"

echo ">> rootfs ready at $ROOTFS"
echo ">> next: pack into a disk image (genimage/guestfish) — see docs/OS-IMAGE.md"
