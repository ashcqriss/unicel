"""Registration of all built-in UNISHELL commands.

Handlers receive the shell context and the parsed argument list. They return a
:class:`CommandResult`; multi-line ``message`` strings are printed line by line
by the calling pane. Side-effecting commands (opening apps, splitting panes)
act on the context and return a short confirmation.
"""

from __future__ import annotations

import datetime as _dt
from typing import Any

from .. import profile as profile_mod
from .. import theme as theme_mod
from ..calc import CalcError, evaluate, format_result
from ..version import PRODUCT_NAME, banner_version
from .registry import CommandRegistry, CommandResult


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _need(value, message: str) -> CommandResult | None:
    return None if value else CommandResult.error(message)


def _pane_number(args: list[str]) -> int | None:
    try:
        return int(args[0])
    except (IndexError, ValueError):
        return None


# --------------------------------------------------------------------------
# command handlers
# --------------------------------------------------------------------------
def _cmd_help(ctx: Any, args: list[str]) -> CommandResult:
    lines = [f"{PRODUCT_NAME} — {banner_version()}", ""]
    for category, commands in ctx.registry.categories().items():
        lines.append(category.upper())
        for command in commands:
            lines.append(f"  {command.help_line()}")
        lines.append("")
    lines.append("Tip: 'cmd cheatsheet' opens the full reference · F1 for hotkeys.")
    return CommandResult.info("\n".join(lines).rstrip())


def _cmd_cmd(ctx: Any, args: list[str]) -> CommandResult:
    if args and args[0] in ("cheatsheet", "sheet", "keys"):
        ctx.open_app("cheatsheet")
        return CommandResult.info("opened Hotkey Cheatsheet")
    return _cmd_help(ctx, args)


def _cmd_version(ctx: Any, args: list[str]) -> CommandResult:
    return CommandResult.info(banner_version())


def _cmd_about(ctx: Any, args: list[str]) -> CommandResult:
    return CommandResult.info(
        f"{PRODUCT_NAME}\n{banner_version()}\n"
        "Terminal-first desktop shell: single-layer panes, UNIX-compatible, "
        "E-Ink/AR profiles."
    )


def _cmd_quit(ctx: Any, args: list[str]) -> CommandResult:
    ctx.quit()
    return CommandResult.info("exiting…")


def _cmd_parabash(ctx: Any, args: list[str]) -> CommandResult:
    if not args:
        ctx.new_parabash()
        return CommandResult.info("opened a new Parabash")
    sub, rest = args[0], args[1:]
    if sub == "new":
        command = " ".join(rest) or None
        pane = ctx.new_parabash(command)
        return CommandResult.info(f"opened Parabash (pane {pane.id})")
    if sub == "split":
        direction = rest[0] if rest else "right"
        pane = ctx.split_parabash(direction)
        return CommandResult.info(f"split {direction}: Parabash (pane {pane.id})")
    if sub in ("hide", "focus", "close"):
        number = _pane_number(rest)
        if number is None:
            return CommandResult.error(f"usage: parabash {sub} <pane-number>")
        ok = {"hide": ctx.manager.hide, "focus": ctx.manager.focus,
              "close": ctx.close_pane}[sub](number)
        return CommandResult.info(f"{sub} pane {number}") if ok else \
            CommandResult.error(f"no pane {number}")
    if sub == "list":
        return _cmd_panes(ctx, [])
    return CommandResult.error("usage: parabash new|split <dir>|hide N|focus N|close N|list")


def _cmd_panes(ctx: Any, args: list[str]) -> CommandResult:
    lines = ["panes:"]
    focused = ctx.manager.focused_id
    for pane in ctx.manager.panes:
        flag = "*" if pane.id == focused else (" " if pane.is_visible else "h")
        state = "visible" if pane.is_visible else "hidden"
        lines.append(f"  {flag} [{pane.id}] {pane.tab_title:<20} {pane.kind:<10} {state}")
    return CommandResult.info("\n".join(lines))


def _cmd_focus(ctx: Any, args: list[str]) -> CommandResult:
    number = _pane_number(args)
    if number is None:
        return CommandResult.error("usage: focus <pane-number>")
    return CommandResult.info(f"focused pane {number}") if ctx.manager.focus(number) \
        else CommandResult.error(f"no pane {number}")


def _cmd_hide(ctx: Any, args: list[str]) -> CommandResult:
    number = _pane_number(args)
    if number is None:
        return CommandResult.error("usage: hide <pane-number>")
    return CommandResult.info(f"hid pane {number}") if ctx.manager.hide(number) \
        else CommandResult.error(f"no pane {number}")


def _cmd_close(ctx: Any, args: list[str]) -> CommandResult:
    number = _pane_number(args)
    if number is None:
        return CommandResult.error("usage: close <pane-number>")
    return CommandResult.info(f"closed pane {number}") if ctx.close_pane(number) \
        else CommandResult.error(f"cannot close pane {number}")


def _cmd_zoom(ctx: Any, args: list[str]) -> CommandResult:
    ctx.manager.toggle_zoom()
    return CommandResult.info("zoom " + ("on" if ctx.manager.zoom else "off"))


def _cmd_split(ctx: Any, args: list[str]) -> CommandResult:
    direction = args[0] if args else "right"
    pane = ctx.split_parabash(direction)
    return CommandResult.info(f"split {direction} (pane {pane.id})")


def _cmd_calc(ctx: Any, args: list[str]) -> CommandResult:
    expression = " ".join(args)
    if not expression:
        ctx.open_app("calculator")
        return CommandResult.info("opened Calculator")
    try:
        return CommandResult.info(f"{expression} = {format_result(evaluate(expression))}")
    except CalcError as exc:
        return CommandResult.error(str(exc))


def _cmd_calendar(ctx: Any, args: list[str]) -> CommandResult:
    if args and args[0] == "today":
        today = _dt.date.today()
        items = ctx.activity.for_date(today.isoformat()) if ctx.activity else []
        lines = [today.strftime("Today is %A, %d %B %Y")]
        if items:
            lines.append("activity:")
            for item in items:
                lines.append(f"  • [{item['type']}] {item['title']}")
        else:
            lines.append("no activity scheduled today")
        return CommandResult.info("\n".join(lines))
    ctx.open_app("calendar")
    return CommandResult.info("opened Calendar")


def _cmd_theme(ctx: Any, args: list[str]) -> CommandResult:
    if not args:
        ctx.open_app("themes")
        return CommandResult.info("opened Theme Library")
    sub = args[0]
    if sub == "list":
        lines = ["themes:"]
        for theme in theme_mod.list_themes():
            mark = "*" if theme.name == ctx.theme.name else " "
            lines.append(f"  {mark} {theme.name:<16} {theme.description}")
        return CommandResult.info("\n".join(lines))
    if sub == "current":
        return CommandResult.info(f"current theme: {ctx.theme.name}")
    if sub == "apply":
        if len(args) < 2:
            return CommandResult.error("usage: theme apply <name>")
        return CommandResult.info(f"applied theme: {args[1]}") if ctx.set_theme(args[1]) \
            else CommandResult.error(f"unknown theme: {args[1]}")
    # `theme <name>` shorthand for apply
    return CommandResult.info(f"applied theme: {sub}") if ctx.set_theme(sub) \
        else CommandResult.error(f"unknown theme: {sub}")


def _cmd_profile(ctx: Any, args: list[str]) -> CommandResult:
    if not args or args[0] == "list":
        lines = ["display profiles:"]
        for prof in profile_mod.PROFILES.values():
            mark = "*" if prof.name == ctx.profile.name else " "
            lines.append(f"  {mark} {prof.name:<10} {prof.description}")
        return CommandResult.info("\n".join(lines))
    if args[0] == "current":
        return CommandResult.info(f"current profile: {ctx.profile.name}")
    name = args[1] if args[0] == "set" and len(args) > 1 else args[0]
    return CommandResult.info(f"profile: {name}") if ctx.set_profile(name) \
        else CommandResult.error(f"unknown profile: {name}")


def _cmd_settings(ctx: Any, args: list[str]) -> CommandResult:
    ctx.open_app("settings")
    return CommandResult.info("opened Settings")


def _cmd_activity(ctx: Any, args: list[str]) -> CommandResult:
    if not args:
        ctx.open_app("activity")
        return CommandResult.info("opened Activity Handler")
    if args[0] == "list":
        items = ctx.activity.all()
        if not items:
            return CommandResult.info("no activity items")
        lines = ["activity:"]
        for item in items:
            mark = "✓" if item.get("status") == "done" else "•"
            lines.append(f"  {mark} [{item['type']}] {item['title']}")
        return CommandResult.info("\n".join(lines))
    if args[0] == "new":
        rest = args[1:]
        item_type = "task"
        if rest and rest[0] in ctx.activity.TYPES:
            item_type = rest[0]
            rest = rest[1:]
        title = " ".join(rest).strip()
        if not title:
            return CommandResult.error('usage: activity new [type] "title"')
        item = ctx.activity.add(item_type, title)
        ctx.open_app("activity")
        return CommandResult.info(f"added {item_type}: {item['title']}")
    return CommandResult.error('usage: activity | activity list | activity new [type] "title"')


def _cmd_notes(ctx: Any, args: list[str]) -> CommandResult:
    if args and args[0] == "new":
        title = " ".join(args[1:]).strip()
        if not title:
            return CommandResult.error('usage: notes new "text"')
        ctx.notes.add(title)
        ctx.open_app("notes")
        return CommandResult.info("note added")
    ctx.open_app("notes")
    return CommandResult.info("opened Notes")


def _cmd_tasks(ctx: Any, args: list[str]) -> CommandResult:
    if args and args[0] == "new":
        title = " ".join(args[1:]).strip()
        if not title:
            return CommandResult.error('usage: tasks new "title"')
        ctx.activity.add("task", title)
        ctx.open_app("tasks")
        return CommandResult.info("task added")
    ctx.open_app("tasks")
    return CommandResult.info("opened Tasks")


def _cmd_web(ctx: Any, args: list[str]) -> CommandResult:
    visual = False
    url_parts = []
    for arg in args:
        if arg in ("--visual", "-v"):
            visual = True
        else:
            url_parts.append(arg)
    url = " ".join(url_parts).strip()
    if not url:
        ctx.open_app("browser")
        return CommandResult.info("opened Browser")
    ctx.open_app("browser", url=url)
    note = " (visual pane not available yet — showing reader view)" if visual else ""
    return CommandResult.info(f"opening {url}{note}")


def _cmd_files(ctx: Any, args: list[str]) -> CommandResult:
    path = " ".join(args) or None
    ctx.open_app("files", path=path)
    return CommandResult.info("opened File Manager")


def _cmd_image(ctx: Any, args: list[str]) -> CommandResult:
    if not args:
        return CommandResult.error("usage: image <path>")
    ctx.open_app("image", path=" ".join(args))
    return CommandResult.info("opened Image Viewer")


def _cmd_media(ctx: Any, args: list[str]) -> CommandResult:
    path = " ".join(args) or None
    ctx.open_app("media", **({"path": path} if path else {}))
    return CommandResult.info("opened Media Viewer")


def _cmd_firewall(ctx: Any, args: list[str]) -> CommandResult:
    if args and args[0] in ("enable", "disable"):
        ctx.config.set("firewall_enabled", args[0] == "enable")
        return CommandResult.info(f"firewall {args[0]}d")
    if args and args[0] == "status":
        enabled = ctx.config.get("firewall_enabled")
        return CommandResult.info(
            f"firewall: {'ENABLED' if enabled else 'DISABLED'} · "
            "policy: INPUT DROP / OUTPUT ACCEPT (default-deny inbound)")
    ctx.open_app("firewall")
    return CommandResult.info("opened Firewall Panel")


def _cmd_users(ctx: Any, args: list[str]) -> CommandResult:
    if args and args[0] == "list":
        users = ctx.users.all()
        if not users:
            return CommandResult.info("no users")
        current = ctx.config.get("current_user")
        lines = ["users:"]
        for user in users:
            mark = "*" if user["name"] == current else " "
            lines.append(f"  {mark} {user['name']} (theme: {user.get('theme') or 'default'})")
        return CommandResult.info("\n".join(lines))
    if args and args[0] == "add":
        name = " ".join(args[1:]).strip()
        if not name:
            return CommandResult.error("usage: users add <name>")
        try:
            ctx.users.add(name)
            ctx.open_app("users")
            return CommandResult.info(f"added user: {name}")
        except ValueError as exc:
            return CommandResult.error(str(exc))
    ctx.open_app("users")
    return CommandResult.info("opened User Manager")


def _cmd_apps(ctx: Any, args: list[str]) -> CommandResult:
    ctx.open_launcher()
    return CommandResult.info("opened App Launcher")


def _cmd_app(ctx: Any, args: list[str]) -> CommandResult:
    if not args:
        ctx.open_launcher()
        return CommandResult.info("opened App Launcher")
    name = args[0]
    if ctx.open_app(name) is None:
        return CommandResult.error(f"unknown app: {name}")
    return CommandResult.info(f"opened {name}")


def _cmd_sysinfo(ctx: Any, args: list[str]) -> CommandResult:
    user = ctx.config.get("current_user") or "—"
    return CommandResult.info(
        f"{banner_version()}\n"
        f"profile : {ctx.profile.name} ({ctx.profile.label})\n"
        f"theme   : {ctx.theme.name}\n"
        f"user    : {user}\n"
        f"panes   : {len(ctx.manager.panes)}\n"
        f"firewall: {'on' if ctx.config.get('firewall_enabled') else 'off'}"
    )


# --------------------------------------------------------------------------
# registration
# --------------------------------------------------------------------------
def register_builtins(registry: CommandRegistry) -> None:
    add = registry.add
    add("help", "List available commands", _cmd_help, "help", category="general")
    add("cmd", "Command reference / cheatsheet", _cmd_cmd, "cmd [cheatsheet]",
        aliases=("commands",), category="general")
    add("version", "Show the UNISHELL version", _cmd_version, "version", category="general")
    add("about", "About E-Console", _cmd_about, "about", category="general")
    add("sysinfo", "Show system status", _cmd_sysinfo, "sysinfo", category="general")
    add("quit", "Exit E-Console", _cmd_quit, "quit", aliases=("exit",), category="general")

    add("parabash", "Manage secondary terminal panes", _cmd_parabash,
        "parabash new|split <dir>|hide N|focus N", aliases=("pb",), category="panes")
    add("panes", "List open panes", _cmd_panes, "panes", category="panes")
    add("focus", "Focus a pane by number", _cmd_focus, "focus N", category="panes")
    add("hide", "Hide a pane by number", _cmd_hide, "hide N", category="panes")
    add("close", "Close a pane by number", _cmd_close, "close N", category="panes")
    add("split", "Split into a new Parabash", _cmd_split, "split <dir>", category="panes")
    add("zoom", "Toggle full-screen pane", _cmd_zoom, "zoom", category="panes")

    add("calc", "Evaluate an expression", _cmd_calc, "calc <expr>", category="apps")
    add("calendar", "Calendar / today", _cmd_calendar, "calendar [today]",
        aliases=("cal",), category="apps")
    add("activity", "Activity Handler", _cmd_activity, 'activity [new [type] "…"]',
        category="apps")
    add("tasks", "Tasks", _cmd_tasks, 'tasks [new "…"]', aliases=("todo",), category="apps")
    add("notes", "Notes", _cmd_notes, 'notes [new "…"]', category="apps")
    add("web", "Open a web page (reader)", _cmd_web, "web [--visual] <url>",
        aliases=("browser",), category="apps")
    add("files", "File manager", _cmd_files, "files [path]", aliases=("lf",), category="apps")
    add("image", "View an image", _cmd_image, "image <path>", category="apps")
    add("media", "Play frame-based media", _cmd_media, "media [path]",
        aliases=("video",), category="apps")
    add("apps", "Open the app launcher", _cmd_apps, "apps", category="apps")
    add("app", "Open a named app", _cmd_app, "app <name>", aliases=("open",), category="apps")

    add("settings", "Open settings", _cmd_settings, "settings", aliases=("config",),
        category="system")
    add("theme", "Theme list/apply", _cmd_theme, "theme list|apply <name>", category="system")
    add("profile", "Display profile", _cmd_profile, "profile list|set <name>", category="system")
    add("firewall", "Firewall panel/status", _cmd_firewall, "firewall [status|enable|disable]",
        aliases=("fw",), category="system")
    add("users", "User manager", _cmd_users, "users [add <name>|list]", category="system")
