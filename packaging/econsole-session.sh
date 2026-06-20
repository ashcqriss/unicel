#!/bin/sh
# E-Console session launcher.
#
# Run on login (or by econsole.service) to start the shell. Keeps E-Console as
# the foreground environment, restarts it if it exits unexpectedly, and drops to
# a plain recovery shell after repeated failures so the device is never bricked
# by a bad update — supporting the "safe recovery mode" reliability goal.

set -u

# UNIX/POSIX defaults expected by E-Console and the apps it launches.
export EDITOR="${EDITOR:-vi}"
export VISUAL="${VISUAL:-vim}"
export PAGER="${PAGER:-less}"
export TERM="${TERM:-econsole}"
# 'econsole' is a custom terminfo alias; fall back to a known-good type if the
# terminfo entry is not installed on this host.
if ! infocmp "$TERM" >/dev/null 2>&1; then
    export TERM=linux
fi

ECONSOLE_CMD="${ECONSOLE_CMD:-python3 -m econsole}"
MAX_FAILS="${ECONSOLE_MAX_FAILS:-3}"
fails=0

while [ "$fails" -lt "$MAX_FAILS" ]; do
    start=$(date +%s)
    # shellcheck disable=SC2086
    $ECONSOLE_CMD
    rc=$?
    end=$(date +%s)

    # Clean exit (user quit) — stop here.
    [ "$rc" -eq 0 ] && exit 0

    # If it ran for a while before dying, treat it as a fresh start.
    if [ "$((end - start))" -ge 30 ]; then
        fails=0
    else
        fails=$((fails + 1))
    fi
    echo "E-Console exited ($rc), restarting [$fails/$MAX_FAILS]..." >&2
    sleep 1
done

echo "E-Console failed repeatedly — dropping to recovery shell." >&2
exec "${SHELL:-/bin/sh}" -l
