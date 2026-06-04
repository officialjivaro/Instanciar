# Instanciar.py
import os
import sys
import warnings

# Keep software OpenGL because it improves general Qt stability on some PCs.
os.environ.setdefault("QT_OPENGL", "software")

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from appdata.gui.main_window import MainWindow


def main():
    warnings.filterwarnings("ignore")
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    # Show after the dashboard appears so GitHub loading never blocks startup.
    QTimer.singleShot(650, window.show_whats_new_if_needed)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
