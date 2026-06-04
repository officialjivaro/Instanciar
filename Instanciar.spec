# Instanciar.spec
# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


PROJECT_ROOT = Path(SPECPATH).resolve()
MAIN_SCRIPT = PROJECT_ROOT / "Instanciar.py"

APPDATA_DIR = PROJECT_ROOT / "appdata"
MEDIA_DIR = APPDATA_DIR / "media"

ICON_ICO = MEDIA_DIR / "icon.ico"
ICON_PNG = MEDIA_DIR / "icon.png"

CUSTOM_QT_RUNTIME_HOOK = PROJECT_ROOT / "pyi_hooks" / "qt_plugins_path_hook.py"


def _require_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Missing {label}: {path}")


def _collect_tree_as_datas(src_root: Path, dest_root: str) -> list[tuple[str, str]]:
    """
    Recursively collect files under src_root and map them into dest_root.

    This is mainly for app media files such as icons.
    """
    root = Path(src_root)
    if not root.exists():
        return []

    datas: list[tuple[str, str]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.name.lower() == "desktop.ini" or path.suffix.lower() in {".pyc", ".pyo"}:
            continue
        if "__pycache__" in path.parts:
            continue

        rel_parent = path.parent.relative_to(root)
        if rel_parent == Path("."):
            dest_dir = dest_root
        else:
            dest_dir = os.path.join(dest_root, str(rel_parent))

        datas.append((str(path), dest_dir))

    return datas


def _dedup_pairs(pairs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []

    for src, dest in pairs:
        key = (os.path.normcase(os.path.abspath(src)), dest)
        if key in seen:
            continue
        seen.add(key)
        out.append((src, dest))

    return out


def _dedup_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []

    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)

    return out


_require_file(MAIN_SCRIPT, "entry script")
_require_file(ICON_ICO, "Windows icon file")

# App media files. This includes icon.ico, icon.png, and future media assets.
project_datas = _collect_tree_as_datas(MEDIA_DIR, "appdata/media")

# Qt plugins needed for the app to look and run correctly on PCs without Python.
# The Qt/... paths match the usual PySide6 wheel layout.
pyside_plugins = collect_data_files(
    "PySide6",
    includes=[
        "Qt/plugins/platforms/*",
        "Qt/plugins/styles/*",
        "Qt/plugins/imageformats/*",
        # Extra fallback patterns. These do nothing if the paths do not exist.
        "plugins/platforms/*",
        "plugins/styles/*",
        "plugins/imageformats/*",
    ],
)

# Selenium has dynamic imports, so keeping Selenium hidden imports is reasonable.
selenium_datas = collect_data_files("selenium")
selenium_hidden = collect_submodules("selenium")

datas = _dedup_pairs(project_datas + pyside_plugins + selenium_datas)

hiddenimports = _dedup_strings(
    selenium_hidden
    + [
        # Keep these explicit without collecting all of PySide6.
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
    ]
)

runtime_hooks = []
if CUSTOM_QT_RUNTIME_HOOK.is_file():
    runtime_hooks.append(str(CUSTOM_QT_RUNTIME_HOOK))

a = Analysis(
    [str(MAIN_SCRIPT)],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=runtime_hooks,
    excludes=[
        "PyQt5",
        "PyQt6",
        "PySide2",
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Instanciar",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON_ICO),
)