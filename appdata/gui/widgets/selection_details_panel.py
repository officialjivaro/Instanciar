# appdata/gui/widgets/selection_details_panel.py
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget, QHBoxLayout, QSizePolicy
from PySide6.QtGui import QFont

from appdata.config.style_constants import (
    BACKGROUND_MAIN,
    TEXT_COLOR,
    GROUP_HOVER,
    ACCENT_COLOR,
    FONT_FAMILY,
    FONT_SIZE,
)


class _DetailRow(QWidget):
    """Simple label/value row used inside the selection details panel."""

    def __init__(self, label, value, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        key_label = QLabel(label, self)
        key_label.setFont(QFont(FONT_FAMILY, FONT_SIZE, QFont.Bold))
        # Slightly wider labels help longer proxy-related row titles fit cleanly.
        key_label.setMinimumWidth(130)

        display_value = "—" if value is None or value == "" else str(value)

        value_label = QLabel(display_value, self)
        value_label.setWordWrap(True)
        value_label.setFont(QFont(FONT_FAMILY, FONT_SIZE))

        layout.addWidget(key_label, 0)
        layout.addWidget(value_label, 1)


class SelectionDetailsPanel(QFrame):
    """Read-only details panel for the current tree selection."""

    _BADGE_COLORS = {
        "info": ACCENT_COLOR,
        "group": ACCENT_COLOR,
        "instance": "#6B7CFF",
        "default": "#3AA3FF",
        "success": "#3FB950",
        "error": "#D04949",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("selectionDetailsPanel")
        self.setMinimumWidth(320)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setStyleSheet(
            f"""
            QFrame#selectionDetailsPanel {{
                background: {BACKGROUND_MAIN};
                border: 1px solid {GROUP_HOVER};
                border-radius: 10px;
            }}
            QLabel {{
                color: {TEXT_COLOR};
                background: transparent;
            }}
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        self.badge_label = QLabel(self)
        self.badge_label.setFont(QFont(FONT_FAMILY, max(FONT_SIZE - 1, 9), QFont.Bold))
        self.badge_label.hide()

        self.title_label = QLabel("Nothing selected", self)
        self.title_label.setWordWrap(True)
        self.title_label.setFont(QFont(FONT_FAMILY, FONT_SIZE + 4, QFont.Bold))

        self.message_label = QLabel("Select a group or instance to see details here.", self)
        self.message_label.setWordWrap(True)
        self.message_label.setFont(QFont(FONT_FAMILY, FONT_SIZE))

        self.rows_host = QWidget(self)
        self.rows_layout = QVBoxLayout(self.rows_host)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(8)

        self.actions_header = QLabel("Available Actions", self)
        self.actions_header.setFont(QFont(FONT_FAMILY, FONT_SIZE + 1, QFont.Bold))

        self.actions_label = QLabel("", self)
        self.actions_label.setWordWrap(True)
        self.actions_label.setFont(QFont(FONT_FAMILY, FONT_SIZE))

        root.addWidget(self.badge_label, 0)
        root.addWidget(self.title_label, 0)
        root.addWidget(self.message_label, 0)
        root.addWidget(self.rows_host, 0)
        root.addWidget(self.actions_header, 0)
        root.addWidget(self.actions_label, 0)
        root.addStretch(1)

    def _clear_rows(self):
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _set_badge(self, text, kind):
        if not text:
            self.badge_label.hide()
            return

        color = self._BADGE_COLORS.get(kind, self._BADGE_COLORS["info"])
        self.badge_label.setText(text.upper())
        self.badge_label.setStyleSheet(
            f"""
            QLabel {{
                background: {color};
                color: white;
                border-radius: 10px;
                padding: 4px 10px;
            }}
            """
        )
        self.badge_label.adjustSize()
        self.badge_label.show()

    def update_details(self, details):
        """Update the panel from a display-ready details dictionary."""
        details = details or {}

        self._set_badge(details.get("badge_text", ""), details.get("badge_kind", "info"))
        self.title_label.setText(details.get("title", "Nothing selected"))
        self.message_label.setText(details.get("message", ""))

        self._clear_rows()
        rows = details.get("rows", [])
        for label, value in rows:
            self.rows_layout.addWidget(_DetailRow(label, value, self.rows_host))
        self.rows_host.setVisible(bool(rows))

        actions_text = (details.get("actions_text") or "").strip()
        self.actions_header.setVisible(bool(actions_text))
        self.actions_label.setVisible(bool(actions_text))
        self.actions_label.setText(actions_text)