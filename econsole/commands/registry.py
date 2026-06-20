"""Command registry and dispatcher for UNISHELL.

Built-in E-Console commands are registered here. Anything not recognised is
reported as unknown so the calling shell can decide whether to pass it through
to the system shell (``/bin/sh``) — that is what makes UNISHELL "terminal-first,
not terminal-only".
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

# A command handler receives the shell context and the parsed argument list and
# returns a CommandResult.
Handler = Callable[[Any, list[str]], "CommandResult"]


@dataclass
class CommandResult:
    ok: bool = True
    message: str = ""
    #: True when no command matched; lets the shell fall through to /bin/sh.
    unknown: bool = False

    @classmethod
    def info(cls, message: str = "") -> "CommandResult":
        return cls(ok=True, message=message)

    @classmethod
    def error(cls, message: str) -> "CommandResult":
        return cls(ok=False, message=message)

    @classmethod
    def not_found(cls, name: str) -> "CommandResult":
        return cls(ok=False, message=f"unknown command: {name}", unknown=True)

    @property
    def lines(self) -> list[str]:
        return self.message.split("\n") if self.message else []


@dataclass
class Command:
    name: str
    summary: str
    handler: Handler
    usage: str = ""
    aliases: tuple[str, ...] = ()
    category: str = "general"

    def help_line(self) -> str:
        usage = self.usage or self.name
        return f"{usage:<28} {self.summary}"


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}
        self._aliases: dict[str, str] = {}

    def register(self, command: Command) -> None:
        self._commands[command.name] = command
        for alias in command.aliases:
            self._aliases[alias] = command.name

    def add(self, name: str, summary: str, handler: Handler, usage: str = "",
            aliases: tuple[str, ...] = (), category: str = "general") -> None:
        self.register(Command(name, summary, handler, usage, aliases, category))

    def resolve(self, name: str) -> Optional[Command]:
        if name in self._commands:
            return self._commands[name]
        if name in self._aliases:
            return self._commands[self._aliases[name]]
        return None

    def all(self) -> list[Command]:
        return sorted(self._commands.values(), key=lambda c: (c.category, c.name))

    def categories(self) -> dict[str, list[Command]]:
        out: dict[str, list[Command]] = {}
        for command in self.all():
            out.setdefault(command.category, []).append(command)
        return out

    def parse(self, line: str) -> list[str]:
        try:
            return shlex.split(line)
        except ValueError:
            # Unbalanced quotes: fall back to a naive split so the user still
            # gets a sensible error rather than a traceback.
            return line.split()

    def dispatch(self, context: Any, line: str) -> CommandResult:
        line = line.strip()
        if not line:
            return CommandResult.info("")
        argv = self.parse(line)
        if not argv:
            return CommandResult.info("")
        name, args = argv[0], argv[1:]
        command = self.resolve(name)
        if command is None:
            return CommandResult.not_found(name)
        try:
            return command.handler(context, args)
        except Exception as exc:  # noqa: BLE001 - a command must never crash the shell
            return CommandResult.error(f"{name}: {exc}")
