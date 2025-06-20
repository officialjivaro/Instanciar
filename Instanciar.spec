# Instanciar.spec
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import PySide6, os

block_cipher = None
pyside_plugins = collect_data_files(
    "PySide6",
    includes=[
        "plugins/platforms/*",
        "plugins/styles/*",
        "plugins/imageformats/*",
    ],
)

a = Analysis(
    ["Instanciar.py"],
    pathex=["."],
    binaries=[],
    datas=[("appdata/media/icon.ico", "appdata/media")] + pyside_plugins,
    hiddenimports=collect_submodules("PySide6"),
    runtime_hooks=["pyi_hooks/qt_plugins_path_hook.py"],
    hooksconfig={},
    cipher=block_cipher,
    noarchive=False,
    optimize=2,
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
    runtime_tmpdir=None,
    console=False,
    icon="appdata/media/icon.ico",
)
