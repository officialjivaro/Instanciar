# appdata/gui/group_manager.py
import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame
from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtCore import Qt
from appdata.logic.group_manager import GroupManagerLogic
from appdata.config.style_constants import BACKGROUND_MAIN, TEXT_COLOR, GROUP_HOVER, ACCENT_COLOR

class GuiGroupManager(QDialog):
    def __init__(self, parent, group_name=None):
        super().__init__(parent)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(BACKGROUND_MAIN))
        palette.setColor(QPalette.WindowText, QColor(TEXT_COLOR))
        palette.setColor(QPalette.Base, QColor(BACKGROUND_MAIN))
        palette.setColor(QPalette.Button, QColor(BACKGROUND_MAIN))
        palette.setColor(QPalette.ButtonText, QColor(TEXT_COLOR))
        self.setPalette(palette)
        self.setFont(QFont("Segoe UI", 11))
        self.setStyleSheet(f"""
            QDialog          {{ background:{BACKGROUND_MAIN}; }}
            QLabel           {{ color:{TEXT_COLOR}; }}
            QLineEdit        {{ background:{GROUP_HOVER}; color:{TEXT_COLOR}; border-radius:3px; padding:4px; }}
            QLineEdit:focus  {{ border:1px solid {ACCENT_COLOR}; }}
            QPushButton      {{ background:{BACKGROUND_MAIN}; color:{TEXT_COLOR}; border:1px solid {GROUP_HOVER}; border-radius:4px; padding:6px 12px; }}
            QPushButton:hover{{ background:{GROUP_HOVER}; border:1px solid {ACCENT_COLOR}; }}
        """)
        self.resize(400, 225)
        self.setModal(True)
        self.setWindowTitle("Group Manager")
        self.group_name = group_name
        self.logic = GroupManagerLogic()
        self.layout = QVBoxLayout(); self.layout.setContentsMargins(20, 20, 20, 20); self.layout.setSpacing(12); self.setLayout(self.layout)
        heading_label = QLabel("Manage Group"); heading_label.setFont(QFont("Segoe UI", 12, QFont.Bold)); heading_label.setAlignment(Qt.AlignHCenter); self.layout.addWidget(heading_label)
        desc_label = QLabel("Create or rename a group to organize your instances."); desc_label.setWordWrap(True); self.layout.addWidget(desc_label)
        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setFrameShadow(QFrame.Sunken); self.layout.addWidget(line)
        self.label = QLabel("Group Name:"); self.name_input = QLineEdit(); self.layout.addWidget(self.label); self.layout.addWidget(self.name_input)
        btn_layout = QHBoxLayout(); self.save_button = QPushButton("Save"); self.cancel_button = QPushButton("Cancel"); btn_layout.addWidget(self.save_button); btn_layout.addWidget(self.cancel_button); self.layout.addLayout(btn_layout)
        self.save_button.clicked.connect(self.on_save); self.cancel_button.clicked.connect(self.reject)
        self.load_existing()
    def resizeEvent(self, event):
        super().resizeEvent(event); 
        if self.isMaximized(): return
        w = self.width(); h = self.height(); ideal_h = int(w * (9/16)); 
        if h != ideal_h: self.resize(w, ideal_h)
    def load_existing(self):
        if self.group_name is not None:
            data = self.logic.get_group(self.group_name)
            if data: self.name_input.setText(data["name"])
    def on_save(self):
        new_name = self.name_input.text().strip()
        if not new_name: self.reject(); return
        if self.group_name is not None: self.logic.edit_group(self.group_name, new_name)
        else: self.logic.create_group(new_name)
        self.accept()
