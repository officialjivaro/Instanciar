# appdata/gui/widgets/command_bar.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Signal

class CommandBar(QWidget):
    launchRequested = Signal()
    editRequested = Signal()
    deleteRequested = Signal()
    duplicateRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        for text, sig in (
            ("Launch", self.launchRequested),
            ("Edit",   self.editRequested),
            ("Delete", self.deleteRequested),
            ("Duplicate", self.duplicateRequested)
        ):
            btn = QPushButton(text, self)
            btn.clicked.connect(sig.emit)
            lay.addWidget(btn)
