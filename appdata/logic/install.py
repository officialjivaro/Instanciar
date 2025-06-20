# appdata/logic/install.py
import os, sys, shutil, getpass, subprocess, ctypes, ctypes.wintypes, winreg, concurrent.futures
from PySide6.QtCore import QObject, Signal

def _shell_create_shortcut(lnk_path: str, exe_path: str):
    vb = f'''
Set sh = CreateObject("WScript.Shell")
Set l = sh.CreateShortcut("{lnk_path.replace("\\", "\\\\")}")
l.TargetPath = "{exe_path.replace("\\", "\\\\")}"
l.IconLocation = "{exe_path.replace("\\", "\\\\")},0"
l.Description = "Instanciar"
l.Save
'''
    tmp = os.path.join(os.getenv("TEMP"), "instanciar_tmp.vbs")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(vb)
    subprocess.run([r"C:\Windows\System32\wscript.exe", tmp], check=True)
    os.remove(tmp)

def _get_desktop():
    buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
    ctypes.windll.shell32.SHGetFolderPathW(None, 0x0010, None, 0, buf)
    return buf.value

class InstallWorker(QObject):
    progress_signal = Signal(int)
    finished_signal = Signal()

    def run_install(self):
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        pool.submit(self._install_chain)
        pool.shutdown(wait=False)

    def _install_chain(self):
        try:
            self._install()
        finally:
            self.finished_signal.emit()

    def _install(self):
        step = self.progress_signal.emit
        usr = getpass.getuser()
        exe_src = sys.executable
        exe_dest = os.path.join("C:\\Users", usr, "Jivaro", "Instanciar", "Instanciar.exe")
        os.makedirs(os.path.dirname(exe_dest), exist_ok=True)
        shutil.copy2(exe_src, exe_dest)
        step(25)

        _shell_create_shortcut(os.path.join(_get_desktop(), "Instanciar.lnk"), exe_dest)
        step(50)

        sm_dir = os.path.join(os.path.expanduser("~"), "AppData", "Roaming",
                              "Microsoft", "Windows", "Start Menu", "Programs", "Jivaro", "Instanciar")
        os.makedirs(sm_dir, exist_ok=True)
        _shell_create_shortcut(os.path.join(sm_dir, "Instanciar.lnk"), exe_dest)
        step(75)

        self._register_uninstall(exe_dest)
        step(100)

    def _register_uninstall(self, exe_path: str):
        usr = getpass.getuser()
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Instanciar")
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "Instanciar")
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, exe_path)
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "0.02")
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Jivaro")
        bat = f'''
@echo off
taskkill /F /IM Instanciar.exe /T >nul 2>&1
rd /s /q "C:\\Users\\{usr}\\Jivaro\\Instanciar" 2>nul
del "%USERPROFILE%\\Desktop\\Instanciar.lnk" 2>nul
rd /s /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Jivaro" 2>nul
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Instanciar" /f 2>nul
'''
        bat_path = os.path.join(os.getenv("TEMP"), "instanciar_uninstall.bat")
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat)
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'cmd /c "{bat_path}"')
        winreg.CloseKey(key)
