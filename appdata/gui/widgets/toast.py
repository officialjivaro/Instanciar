# appdata/gui/widgets/toast.py
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PySide6.QtGui import QFont
from appdata.config.style_constants import BACKGROUND_MAIN, TEXT_COLOR, FONT_FAMILY, FONT_SIZE

class ToastWidget(QWidget):
    def __init__(self, text, duration, parent=None):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setStyleSheet(f"background:{BACKGROUND_MAIN};color:{TEXT_COLOR};border-radius:6px;")
        lay = QVBoxLayout(self); lay.setContentsMargins(20, 12, 20, 12)
        lbl = QLabel(text); lbl.setFont(QFont(FONT_FAMILY, FONT_SIZE + 2, QFont.Bold)); lay.addWidget(lbl)
        self.adjustSize()
        self._anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._anim.setDuration(300); self._anim.setStartValue(0); self._anim.setEndValue(1)
        self._anim.setEasingCurve(QEasingCurve.OutCubic); self._anim.start()
        QTimer.singleShot(duration, self._fade)
    def _fade(self):
        self._anim.setDirection(QPropertyAnimation.Backward)
        self._anim.finished.connect(self.close); self._anim.start()

class ToastCenter:
    _inst = None
    def __new__(cls):
        if not cls._inst:
            cls._inst = super().__new__(cls)
            cls._inst._stack = []
        return cls._inst
    def show(self, text, duration=4000, anchor_widget=None):
        tw = ToastWidget(text, duration)
        if anchor_widget:
            tw.adjustSize()
            center = anchor_widget.frameGeometry().center()
            tw.move(center.x() - tw.width() // 2,
                    center.y() - tw.height() // 2)
        else:
            scr = QApplication.primaryScreen().availableGeometry()
            offset = sum(w.height() + 8 for w in self._stack)
            tw.move(scr.right() - tw.width() - 20,
                    scr.bottom() - tw.height() - 20 - offset)
        tw.show()
        self._stack.append(tw)
        tw.destroyed.connect(lambda: self._stack.remove(tw) if tw in self._stack else None)
