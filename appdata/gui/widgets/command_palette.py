# appdata/gui/widgets/command_palette.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem
from rapidfuzz import process

class CommandPalette(QDialog):
    def __init__(self, actions: dict, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.actions = actions
        lay = QVBoxLayout(self)
        self.inp = QLineEdit()
        self.lst = QListWidget()
        lay.addWidget(self.inp)
        lay.addWidget(self.lst)
        self.inp.textChanged.connect(self._refresh)
        self.lst.itemActivated.connect(self._trigger)
        self._refresh("")

    def _refresh(self, txt):
        self.lst.clear()
        choices = process.extract(txt, self.actions.keys(), limit=15, score_cutoff=40) if txt else [(k, 100) for k in self.actions]
        for k, _ in choices:
            QListWidgetItem(k, self.lst)

    def _trigger(self, item):
        self.actions[item.text()]()
        self.accept()
