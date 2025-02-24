# instanciar.py
import sys
import re
import urllib.request
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from appdata.gui.main_window import MainWindow
from appdata.version.version import VERSION as LOCAL_VERSION

def check_for_updates():
    url = "https://raw.githubusercontent.com/officialjivaro/Instanciar/main/appdata/version/version.py"
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read().decode("utf-8")
        match = re.search(r'VERSION\s*=\s*[\'"]([^\'"]+)[\'"]', data)
        if match:
            remote_str = match.group(1).strip()
            local_str = LOCAL_VERSION.strip()
            local_num = local_str.lower().replace("v","")
            remote_num = remote_str.lower().replace("v","")
            try:
                if float(local_num) < float(remote_num):
                    app = QApplication.instance()
                    if not app:
                        app = QApplication(sys.argv)
                    box = QMessageBox()
                    box.setWindowTitle("Update Available")
                    box.setText(
                        f"A newer version ({remote_str}) is available. You have {local_str}.\n"
                        "Do you want to download it now?"
                    )
                    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    result = box.exec()
                    if result == QMessageBox.Yes:
                        QDesktopServices.openUrl(QUrl("https://jivaro.net/downloads/programs/info/instanciar"))
            except ValueError:
                pass
    except Exception:
        pass

def main():
    app = QApplication(sys.argv)
    check_for_updates()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
