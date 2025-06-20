# appdata/gui/widgets/lottie_stub.py
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QMovie

class LottieWidget(QLabel):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self._movie = QMovie("appdata/media/install_fallback.gif")
        self.setMovie(self._movie)
        self._movie.start()
    def setProgress(self, _): pass
