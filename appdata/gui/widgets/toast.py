# appdata/gui/widgets/toast.py
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PySide6.QtGui import QFont

from appdata.config.style_constants import (
    BACKGROUND_MAIN,
    TEXT_COLOR,
    GROUP_HOVER,
    ACCENT_COLOR,
    FONT_FAMILY,
    FONT_SIZE,
)


_TOAST_THEMES = {
    "info": {"accent": ACCENT_COLOR, "label": "Info", "duration": 3200},
    "success": {"accent": "#3FB950", "label": "Success", "duration": 3200},
    "error": {"accent": "#D04949", "label": "Error", "duration": 5200},
}


class ToastWidget(QWidget):
    """Floating toast widget with typed feedback styling."""

    def __init__(self, text, duration, kind="info", parent=None):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint)
        self.setObjectName("toastWidget")
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        theme = _TOAST_THEMES.get(kind, _TOAST_THEMES["info"])

        self.setStyleSheet(
            f"""
            QWidget#toastWidget {{
                background: {BACKGROUND_MAIN};
                color: {TEXT_COLOR};
                border: 1px solid {GROUP_HOVER};
                border-left: 4px solid {theme["accent"]};
                border-radius: 8px;
            }}
            QLabel#toastKind {{
                color: {theme["accent"]};
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        kind_label = QLabel(theme["label"].upper(), self)
        kind_label.setObjectName("toastKind")
        kind_label.setFont(QFont(FONT_FAMILY, max(FONT_SIZE - 1, 9), QFont.Bold))

        body_label = QLabel(text, self)
        body_label.setWordWrap(True)
        body_label.setMaximumWidth(360)
        body_label.setFont(QFont(FONT_FAMILY, FONT_SIZE + 1, QFont.Bold))

        layout.addWidget(kind_label)
        layout.addWidget(body_label)

        self.setWindowOpacity(0.0)
        self.adjustSize()

        self._anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._anim.setDuration(220)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()

        QTimer.singleShot(duration, self._fade)

    def _fade(self):
        self._anim.setDirection(QPropertyAnimation.Backward)
        self._anim.finished.connect(self.close)
        self._anim.start()


class ToastCenter:
    """Singleton-style toast manager that stacks floating notifications."""

    _inst = None

    def __new__(cls):
        if not cls._inst:
            cls._inst = super().__new__(cls)
            cls._inst._stack = []
        return cls._inst

    def show(self, text, duration=None, anchor_widget=None, kind="info"):
        theme = _TOAST_THEMES.get(kind, _TOAST_THEMES["info"])
        tw = ToastWidget(text, duration or theme["duration"], kind=kind)

        offset = sum(w.height() + 10 for w in self._stack if w is not None)

        if anchor_widget:
            tw.adjustSize()
            anchor = anchor_widget.frameGeometry()
            tw.move(
                anchor.center().x() - tw.width() // 2,
                anchor.bottom() - tw.height() - 24 - offset,
            )
        else:
            screen = QApplication.primaryScreen().availableGeometry()
            tw.move(
                screen.right() - tw.width() - 20,
                screen.bottom() - tw.height() - 20 - offset,
            )

        tw.show()
        tw.raise_()
        self._stack.append(tw)
        tw.destroyed.connect(lambda: self._stack.remove(tw) if tw in self._stack else None)