# instanciar.py
import os, sys, re, urllib.request, warnings
os.environ.setdefault("QTWEBENGINE_DISABLE_GPU", "1")
os.environ.setdefault("QTWEBENGINE_DISABLE_GPU_THREAD", "1")
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu --disable-gpu-compositing --disable-features=WebGPU,Accelerated2dCanvas")
os.environ.setdefault("QT_OPENGL", "software")
os.environ.setdefault("QT_LOGGING_RULES", "qt.webenginecontext.debug=false")

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from appdata.gui.main_window import MainWindow
from appdata.version.version import VERSION as LOCAL_VERSION
from appdata.utils.version_parser import parse_version_string


def _remote_version():
    url = "https://raw.githubusercontent.com/officialjivaro/Instanciar/main/appdata/version/version.py"
    try:
        with urllib.request.urlopen(url) as r:
            m = re.search(r'VERSION\s*=\s*[\'"]([^\'"]+)[\'"]', r.read().decode())
            return m.group(1).strip() if m else None
    except Exception:
        return None


def main():
    warnings.filterwarnings("ignore")
    app = QApplication(sys.argv)
    remote = _remote_version()
    local = LOCAL_VERSION.strip()
    if remote and parse_version_string(remote) > parse_version_string(local):
        box = QMessageBox()
        box.setWindowTitle("Update Available")
        box.setText(f"A newer version ({remote}) is available. You have {local}.\nDownload now?")
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        if box.exec() == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl("https://jivaro.net/downloads/programs/info/instanciar"))
    MainWindow().show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
