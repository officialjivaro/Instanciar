# pyi_hooks/qt_plugins_path_hook.py
import os, sys
plugins_dir = os.path.join(sys._MEIPASS, "PySide6", "plugins")
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugins_dir