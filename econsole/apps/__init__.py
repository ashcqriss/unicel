"""Built-in E-Console apps and the app registry.

Each app is a :class:`~econsole.apps.base.AppPane`. The registry maps the names
used by the ``app`` / ``open`` commands (and the app launcher) to factory
callables. Adding an app is a one-line registration here.
"""

from __future__ import annotations

from typing import Any, Callable

from .base import AppPane
from .activity import ActivityApp
from .browser import BrowserApp
from .calculator import CalculatorApp
from .calendar import CalendarApp
from .cheatsheet import CheatsheetApp
from .filemanager import FileManagerApp
from .firewall import FirewallApp
from .imagepane import ImageApp
from .media import MediaApp
from .notes import NotesApp
from .settings import SettingsApp
from .tasks import TasksApp
from .themelib import ThemeLibraryApp
from .usermanager import UserManagerApp

AppFactory = Callable[..., AppPane]


class AppInfo:
    def __init__(self, name: str, label: str, factory: AppFactory,
                 aliases: tuple[str, ...] = (), description: str = ""):
        self.name = name
        self.label = label
        self.factory = factory
        self.aliases = aliases
        self.description = description


APPS: dict[str, AppInfo] = {}
_ALIASES: dict[str, str] = {}


def register(info: AppInfo) -> None:
    APPS[info.name] = info
    for alias in info.aliases:
        _ALIASES[alias] = info.name


def resolve(name: str) -> AppInfo | None:
    name = name.lower()
    if name in APPS:
        return APPS[name]
    if name in _ALIASES:
        return APPS[_ALIASES[name]]
    return None


def create(name: str, context: Any, **kwargs) -> AppPane | None:
    info = resolve(name)
    if info is None:
        return None
    return info.factory(context=context, **kwargs)


register(AppInfo("calculator", "Calculator", CalculatorApp, ("calc-app",),
                 "Arithmetic calculator with history."))
register(AppInfo("calendar", "Calendar", CalendarApp, ("cal",),
                 "Month calendar with activity markers."))
register(AppInfo("activity", "Activity Handler", ActivityApp, ("act",),
                 "Unified tasks, habits, reminders, events, goals, projects."))
register(AppInfo("tasks", "Tasks", TasksApp, ("task", "todo"),
                 "Task list (a view of the Activity Handler)."))
register(AppInfo("notes", "Notes", NotesApp, ("note",),
                 "Quick notes."))
register(AppInfo("settings", "Settings", SettingsApp, ("config",),
                 "System settings: profile, theme, firewall, updates."))
register(AppInfo("themes", "Theme Library", ThemeLibraryApp, ("theme-lib",),
                 "Browse and apply themes."))
register(AppInfo("cheatsheet", "Hotkey Cheatsheet", CheatsheetApp, ("keys", "help-app"),
                 "Hotkeys and command reference."))
register(AppInfo("users", "User Manager", UserManagerApp, ("user",),
                 "Local user register (max 3)."))
register(AppInfo("firewall", "Firewall Panel", FirewallApp, ("fw",),
                 "Firewall status and rules."))
register(AppInfo("files", "File Manager", FileManagerApp, ("fm", "lf"),
                 "Browse the filesystem."))
register(AppInfo("browser", "Browser", BrowserApp, ("web-app",),
                 "Text-mode web reader."))
register(AppInfo("image", "Image Viewer", ImageApp, ("img",),
                 "Inline image renderer (ASCII / half-block)."))
register(AppInfo("media", "Media Viewer", MediaApp, ("video",),
                 "Low-FPS frame-based video/animation output."))

__all__ = ["AppPane", "AppInfo", "APPS", "register", "resolve", "create"]
