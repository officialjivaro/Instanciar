# appdata/gui/progress_bar.py
import sys
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt

class InstallProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Installing Instanciar")
        self.setWindowModality(Qt.ApplicationModal)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.label = QLabel("Installing, please wait...")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        self.resize(300, 100)

    def update_progress(self, val):
        self.progress_bar.setValue(val)
