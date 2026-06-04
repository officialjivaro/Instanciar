# appdata/gui/widgets/selection_details_panel.py
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
)

from appdata.config.style_constants import FONT_FAMILY, FONT_SIZE
from appdata.gui.themes.app_theme import set_widget_role, set_widget_state


class _ElideLabel(QLabel):
    """One-line label that shortens long text instead of forcing scrollbars."""

    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self._full_text = ""
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumWidth(40)
        self.setWordWrap(False)
        self.set_full_text(text)

    def set_full_text(self, text):
        self._full_text = "—" if text is None or text == "" else str(text)
        self.setToolTip(self._full_text)
        self._update_elide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_elide()

    def _update_elide(self):
        width = max(20, self.width())
        self.setText(self.fontMetrics().elidedText(self._full_text, Qt.ElideRight, width))


class _DetailRow(QFrame):
    """Compact key/value row for the inspector panel."""

    def __init__(self, label, value, parent=None):
        super().__init__(parent)
        self.setObjectName("DetailRow")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QGridLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(0)

        key_label = QLabel(str(label), self)
        key_label.setWordWrap(False)
        key_label.setFont(QFont(FONT_FAMILY, max(FONT_SIZE - 1, 9), QFont.Bold))
        key_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        key_label.setMinimumWidth(108)
        key_label.setMaximumWidth(132)
        set_widget_role(key_label, "detailKey")

        value_label = _ElideLabel(value, self)
        value_label.setFont(QFont(FONT_FAMILY, FONT_SIZE))
        set_widget_role(value_label, "detailValue")

        if "warning" in str(label).casefold() or "issue" in str(label).casefold():
            set_widget_state(value_label, "warning")

        layout.addWidget(key_label, 0, 0)
        layout.addWidget(value_label, 0, 1)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)


class SelectionDetailsPanel(QFrame):
    """No-scroll inspector for the current tree selection.

    Long values are shortened with a tooltip instead of stretching the panel or
    adding scrollbars. This keeps the dashboard stable at the 1280x720 minimum.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("selectionDetailsPanel")
        self.setMinimumWidth(320)
        self.setMaximumWidth(430)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        self.badge_label = QLabel(self)
        self.badge_label.setObjectName("SelectionBadge")
        self.badge_label.setFont(QFont(FONT_FAMILY, max(FONT_SIZE - 1, 9), QFont.Bold))
        self.badge_label.setWordWrap(False)
        self.badge_label.hide()

        self.title_label = _ElideLabel("Nothing selected", self)
        self.title_label.setObjectName("DetailsTitle")
        self.title_label.setFont(QFont(FONT_FAMILY, FONT_SIZE + 4, QFont.Bold))

        self.message_label = QLabel("Select a group or instance to see details here.", self)
        self.message_label.setWordWrap(True)
        self.message_label.setFont(QFont(FONT_FAMILY, FONT_SIZE))
        self.message_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.message_label.setMaximumHeight(58)
        set_widget_role(self.message_label, "detailValue")

        self.rows_host = QFrame(self)
        self.rows_host.setObjectName("DetailsRowsHost")
        self.rows_host.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.rows_layout = QVBoxLayout(self.rows_host)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(5)

        self.actions_header = QLabel("Available Actions", self)
        self.actions_header.setFont(QFont(FONT_FAMILY, FONT_SIZE + 1, QFont.Bold))
        self.actions_header.setWordWrap(False)
        set_widget_role(self.actions_header, "sectionTitle")

        self.actions_label = QLabel("", self)
        self.actions_label.setWordWrap(True)
        self.actions_label.setFont(QFont(FONT_FAMILY, FONT_SIZE))
        self.actions_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.actions_label.setMaximumHeight(54)
        set_widget_role(self.actions_label, "detailValue")

        root.addWidget(self.badge_label, 0)
        root.addWidget(self.title_label, 0)
        root.addWidget(self.message_label, 0)
        root.addWidget(self.rows_host, 0)
        root.addStretch(1)
        root.addWidget(self.actions_header, 0)
        root.addWidget(self.actions_label, 0)

    def _clear_rows(self):
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def update_details(self, details: dict) -> None:
        details = details or {}
        self._clear_rows()

        badge_text = str(details.get("badge_text") or "").strip()
        badge_kind = str(details.get("badge_kind") or "info").strip() or "info"
        if badge_text:
            self.badge_label.setText(badge_text.upper())
            self.badge_label.show()
            set_widget_state(self.badge_label, badge_kind)
        else:
            self.badge_label.hide()

        self.title_label.set_full_text(str(details.get("title") or "Nothing selected"))
        self.message_label.setText(str(details.get("message") or ""))
        self.actions_label.setText(str(details.get("actions_text") or ""))

        rows = list(details.get("rows", []))
        # Keep the inspector stable without scrollbars. Extra details remain
        # available in the selected row's tooltip when individual values are long.
        max_rows = 9 if self.height() >= 620 else 7
        for label, value in rows[:max_rows]:
            self.rows_layout.addWidget(_DetailRow(label, value, self.rows_host))

        if len(rows) > max_rows:
            self.rows_layout.addWidget(_DetailRow("More", f"{len(rows) - max_rows} additional details in edit view", self.rows_host))
