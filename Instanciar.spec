# Instanciar.spec
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

pyside_plugins = collect_data_files(
    "PySide6",
    includes=[
        "plugins/platforms/*",
        "plugins/styles/*",
        "plugins/imageformats/*",
    ],
)

selenium_datas = collect_data_files("selenium")
selenium_hidden = collect_submodules("selenium")

a = Analysis(
    ["Instanciar.py"],
    pathex=["."],
    binaries=[],
    datas=[("appdata/media/icon.ico", "appdata/media")] + pyside_plugins + selenium_datas,
    hiddenimports=collect_submodules("PySide6") + selenium_hidden,
    runtime_hooks=["pyi_hooks/qt_plugins_path_hook.py"],
    hooksconfig={},
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