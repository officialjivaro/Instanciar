# appdata/logic/install.py
import os
import sys
import shutil
import getpass
import winreg
import subprocess
import ctypes
import ctypes.wintypes
from PySide6.QtCore import QObject, Signal

def get_desktop_folder():
    CSIDL_DESKTOPDIRECTORY = 0x0010
    SHGFP_TYPE_CURRENT = 0
    buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
    ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOPDIRECTORY, None, SHGFP_TYPE_CURRENT, buf)
    return buf.value

class InstallWorker(QObject):
    progress_signal = Signal(int)
    finished_signal = Signal()

    def run_install(self):
        try:
            self.install_instanciar()
        except:
            pass
        self.finished_signal.emit()

    def install_instanciar(self):
        self.progress_signal.emit(10)
        user = getpass.getuser()
        exe_src = sys.executable
        exe_dest = f"C:\\Users\\{user}\\Jivaro\\Instanciar\\Instanciar.exe"
        if not os.path.exists(os.path.dirname(exe_dest)):
            os.makedirs(os.path.dirname(exe_dest))
        shutil.copyfile(exe_src, exe_dest)
        self.progress_signal.emit(40)
        create_desktop_shortcut(exe_dest)
        self.progress_signal.emit(70)
        create_startmenu_shortcut(exe_dest)
        register_uninstall(exe_dest)
        self.progress_signal.emit(100)

def install_instanciar():
    w = InstallWorker()
    w.run_install()

def create_desktop_shortcut(exe_path):
    d = get_desktop_folder()
    s = os.path.join(d, "Instanciar.lnk")
    ws = r"C:\Windows\System32\wscript.exe"
    sc = s.replace("\\","\\\\")
    ex = exe_path.replace("\\","\\\\")
    vb = f'''
Set shell = CreateObject("WScript.Shell")
Set link = shell.CreateShortcut("{sc}")
link.TargetPath = "{ex}"
link.IconLocation = "{ex},0"
link.Description = "Instanciar"
link.Save
'''
    tmp = os.path.join(os.getenv("TEMP"), "instanciar_desktop.vbs")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(vb)
    subprocess.run([ws, tmp], check=True)
    os.remove(tmp)

def create_startmenu_shortcut(exe_path):
    up = os.path.expanduser("~")
    j = os.path.join(up,"AppData","Roaming","Microsoft","Windows","Start Menu","Programs","Jivaro")
    if not os.path.exists(j):
        os.makedirs(j)
    inst = os.path.join(j, "Instanciar")
    if not os.path.exists(inst):
        os.makedirs(inst)
    s = os.path.join(inst, "Instanciar.lnk")
    ws = r"C:\Windows\System32\wscript.exe"
    sc = s.replace("\\","\\\\")
    ex = exe_path.replace("\\","\\\\")
    vb = f'''
Set shell = CreateObject("WScript.Shell")
Set link = shell.CreateShortcut("{sc}")
link.TargetPath = "{ex}"
link.IconLocation = "{ex},0"
link.Description = "Instanciar"
link.Save
'''
    tmp = os.path.join(os.getenv("TEMP"), "instanciar_start.vbs")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(vb)
    subprocess.run([ws, tmp], check=True)
    os.remove(tmp)

def register_uninstall(exe_path):
    user = getpass.getuser()
    h = winreg.CreateKey(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Instanciar")
    winreg.SetValueEx(h,"DisplayName",0,winreg.REG_SZ,"Instanciar")
    winreg.SetValueEx(h,"DisplayIcon",0,winreg.REG_SZ,exe_path)
    winreg.SetValueEx(h,"DisplayVersion",0,winreg.REG_SZ,"0.02")
    winreg.SetValueEx(h,"Publisher",0,winreg.REG_SZ,"Jivaro")
    b = f'''
@echo off
taskkill /F /IM Instanciar.exe /T
if exist "C:\\Users\\{user}\\Jivaro\\Instanciar\\Instanciar.exe" del "C:\\Users\\{user}\\Jivaro\\Instanciar\\Instanciar.exe"
if exist "%USERPROFILE%\\Desktop\\Instanciar.lnk" del "%USERPROFILE%\\Desktop\\Instanciar.lnk"
if exist "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Jivaro\\Instanciar\\Instanciar.lnk" del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Jivaro\\Instanciar\\Instanciar.lnk"
if exist "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Jivaro\\Instanciar" rmdir /s /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Jivaro\\Instanciar"
if exist "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Jivaro" rmdir /s /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Jivaro"
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Instanciar" /f
exit
'''
    bf = os.path.join(os.getenv("TEMP"), "instanciar_uninstall.bat")
    with open(bf, "w", encoding="utf-8") as f:
        f.write(b)
    u = f'cmd /c "{bf}"'
    winreg.SetValueEx(h,"UninstallString",0,winreg.REG_SZ,u)
    winreg.CloseKey(h)
