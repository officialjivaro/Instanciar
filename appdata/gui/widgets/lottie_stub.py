# appdata/gui/widgets/lottie_stub.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy


class LottieWidget(QLabel):
    """Small install-progress visual that does not depend on missing media files.

    Older builds pointed this widget at appdata/media/install_fallback.gif, but
    that file is not part of the release package. A text-based indicator is
    safer and works in source and one-file EXE builds.
    """

    def __init__(self, path=None, parent=None):
        super().__init__(parent)
        self.setObjectName("InstallProgressVisual")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(92)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setText("Installing…")

    def setProgress(self, value):
        try:
            pct = max(0, min(100, int(round(float(value) * 100))))
        except Exception:
            pct = 0
        self.setText(f"Installing… {pct}%")
