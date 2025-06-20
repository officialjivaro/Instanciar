# appdata/utils/windows_effects.py
import ctypes, platform, ctypes.wintypes
from PySide6.QtCore import Qt

def enable_mica(window):
    if platform.system() != "Windows":
        return
    try:
        DWMWA_SYSTEMBACKDROP_TYPE = 38
        DWMSBT_MAINWINDOW = 2
        hwnd = int(window.winId())
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.wintypes.HWND(hwnd),
            ctypes.wintypes.DWORD(DWMWA_SYSTEMBACKDROP_TYPE),
            ctypes.byref(ctypes.wintypes.DWORD(DWMSBT_MAINWINDOW)),
            ctypes.sizeof(ctypes.wintypes.DWORD),
        )
        window.setAttribute(Qt.WA_TranslucentBackground, True)
    except Exception:
        pass
