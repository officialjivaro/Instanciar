# appdata/gui/widgets/progress_bar.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from appdata.gui.widgets.lottie_stub import LottieWidget

class InstallProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Installing Instanciar")
        self.setWindowModality(Qt.ApplicationModal)
        lay = QVBoxLayout(self)
        self.lottie = LottieWidget("appdata/media/install_anim.json")
        lay.addWidget(self.lottie)
        self.percent = QLabel("0 %")
        self.percent.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.percent)
        self.resize(380, 240)

    def update_progress(self, val: int):
        self.percent.setText(f"{val} %")
        self.lottie.setProgress(val / 100)
