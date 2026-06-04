# appdata/gui/widgets/progress_bar.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout

from appdata.config.style_constants import CARD_BACKGROUND, TEXT_COLOR
from appdata.gui.themes.app_theme import apply_app_theme
from appdata.gui.widgets.lottie_stub import LottieWidget


class InstallProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DialogRoot")
        self.setWindowTitle("Installing Instanciar")
        self.setWindowModality(Qt.ApplicationModal)
        apply_app_theme(self)

        self.setStyleSheet(
            f"""
            QDialog#DialogRoot {{
                background: {CARD_BACKGROUND};
                color: {TEXT_COLOR};
            }}
            QLabel {{
                color: {TEXT_COLOR};
                background: transparent;
                font-weight: 800;
            }}
            """
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(12)

        self.lottie = LottieWidget("appdata/media/install_anim.json")
        lay.addWidget(self.lottie)

        self.percent = QLabel("0 %")
        self.percent.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.percent)

        self.resize(380, 240)

    def update_progress(self, val: int):
        self.percent.setText(f"{val} %")
        self.lottie.setProgress(val / 100)
