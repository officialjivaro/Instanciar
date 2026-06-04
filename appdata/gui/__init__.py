# File: appdata/gui/__init__.py
"""
GUI package.

`MainWindow` is exposed lazily to reduce import-time side effects and help avoid
circular import issues during application startup.
"""

from __future__ import annotations

from typing import Any

__all__ = ["MainWindow"]


def __getattr__(name: str) -> Any:
    """Lazily resolve public symbols to prevent import-time circular dependencies."""
    if name == "MainWindow":
        from appdata.gui.main_window import MainWindow

        return MainWindow
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
