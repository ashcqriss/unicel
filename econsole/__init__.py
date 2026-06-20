"""E-Console: a terminal-first desktop shell.

The package exposes the application entry point and the version. Everything else
lives in focused submodules (panes, apps, commands, ...).
"""

from .version import PRODUCT_NAME, SHELL_NAME, VERSION, banner_version

__all__ = ["VERSION", "SHELL_NAME", "PRODUCT_NAME", "banner_version", "main"]


def main(argv=None) -> int:
    """Lazily import the app so ``import econsole`` stays light."""
    from .app import main as _main
    return _main(argv)
