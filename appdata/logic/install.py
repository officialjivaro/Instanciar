# appdata/logic/install.py
import os
import sys
import shutil
import getpass
import winreg
import subprocess

def install_instanciar():
    u = getpass.getuser()
    s = sys.executable
    d = f"C:\\Users\\{u}\\Jivaro\\Instanciar\\Instanciar.exe"
    if not os.path.exists(os.path.dirname(d)):
        os.makedirs(os.path.dirname(d))
    shutil.copyfile(s, d)
    create_desktop_shortcut(d)
    create_startmenu_shortcut(d)
    register_uninstall(d)

def create_desktop_shortcut(e):
    ds = os.path.join(os.path.join(os.path.expanduser("~")), "Desktop")
    sc = os.path.join(ds, "Instanciar.lnk")
    wscript = r"C:\Windows\System32\wscript.exe"
    vbs = f'''Set s = CreateObject("WScript.Shell")
Set l = s.CreateShortcut("{sc}")
l.TargetPath = "{e}"
l.IconLocation = "{e},0"
l.Description = "Instanciar"
l.Save'''
    vbspath = os.path.join(os.getenv("TEMP"), "instanciar_desktop.vbs")
    with open(vbspath, "w", encoding="utf-8") as f:
        f.write(vbs)
    subprocess.run([wscript, vbspath], check=True)
    os.remove(vbspath)

def create_startmenu_shortcut(e):
    sm = os.path.join(os.path.join(os.path.expanduser("~")), "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "Jivaro")
    if not os.path.exists(sm):
        os.makedirs(sm)
    sc = os.path.join(sm, "Instanciar.lnk")
    wscript = r"C:\Windows\System32\wscript.exe"
    vbs = f'''Set s = CreateObject("WScript.Shell")
Set l = s.CreateShortcut("{sc}")
l.TargetPath = "{e}"
l.IconLocation = "{e},0"
l.Description = "Instanciar"
l.Save'''
    vbspath = os.path.join(os.getenv("TEMP"), "instanciar_start.vbs")
    with open(vbspath, "w", encoding="utf-8") as f:
        f.write(vbs)
    subprocess.run([wscript, vbspath], check=True)
    os.remove(vbspath)

def register_uninstall(e):
    r = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Instanciar")
    winreg.SetValueEx(r, "DisplayName", 0, winreg.REG_SZ, "Instanciar")
    winreg.SetValueEx(r, "DisplayIcon", 0, winreg.REG_SZ, e)
    winreg.SetValueEx(r, "DisplayVersion", 0, winreg.REG_SZ, "0.02")
    winreg.SetValueEx(r, "Publisher", 0, winreg.REG_SZ, "Jivaro")
    winreg.SetValueEx(r, "UninstallString", 0, winreg.REG_SZ, f'"{sys.executable}" -c "import os;import sys;import shutil;import winreg;import getpass;p=getpass.getuser();d=f\\"C:\\\\Users\\\\{{p}}\\\\Jivaro\\\\Instanciar\\\\Instanciar.exe\\";os.remove(d) if os.path.exists(d) else None;ds=os.path.join(os.path.join(os.path.expanduser(\\"~\\")),\\"Desktop\\",\\"Instanciar.lnk\\");os.remove(ds) if os.path.exists(ds) else None;sm=os.path.join(os.path.join(os.path.expanduser(\\"~\\")),\\"AppData\\",\\"Roaming\\",\\"Microsoft\\",\\"Windows\\",\\"Start Menu\\",\\"Programs\\",\\"Jivaro\\",\\"Instanciar.lnk\\");os.remove(sm) if os.path.exists(sm) else None;winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r\\"Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\Instanciar\\")"')
    winreg.CloseKey(r)
