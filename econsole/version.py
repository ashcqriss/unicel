"""E-Console / UNISHELL version information.

A single source of truth for the version string shown in the UNISHELL banner
and in the persistent upper-left tab.
"""

# Semantic-ish version for the E-Console shell prototype.
VERSION = "0.1.0"

# Marketing / banner name of the root shell.
SHELL_NAME = "UNISHELL"

# Full product name.
PRODUCT_NAME = "E-Console OS"


def banner_version() -> str:
    """Return the string used in the UNISHELL banner, e.g. ``UNISHELL v0.1.0``."""
    return f"{SHELL_NAME} v{VERSION}"


def tab_label() -> str:
    """Return the compact label for the persistent upper-left tab."""
    return f"{SHELL_NAME} v{VERSION}"
