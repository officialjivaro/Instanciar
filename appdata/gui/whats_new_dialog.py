# appdata/gui/whats_new_dialog.py
"""What's New dialog for live Instanciar release notes."""

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from appdata.gui.themes.app_theme import apply_app_theme, set_widget_role
from appdata.logic.whats_new_service import WhatsNewContent


class WhatsNewDialog(QDialog):
    """Display the current live Instanciar release notes or a GitHub load error."""

    def __init__(self, content: WhatsNewContent, parent=None, *, allow_suppress: bool = True):
        super().__init__(parent)
        self.content = content
        self.allow_suppress = bool(allow_suppress and content.is_remote)

        self.setObjectName("WhatsNewDialogRoot")
        self.setWindowTitle(content.title or "What’s New in Instanciar")
        self.resize(780, 620)
        self.setMinimumSize(720, 520)

        apply_app_theme(self)
        self._build_ui()

    # Section Name | Build dialog UI
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        header = QFrame(self)
        header.setObjectName("WhatsNewHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 14, 16, 14)
        header_layout.setSpacing(4)

        eyebrow = QLabel("Instanciar updates", header)
        set_widget_role(eyebrow, "eyebrow")

        title = QLabel(self.content.title or "What’s New in Instanciar", header)
        title.setWordWrap(True)
        set_widget_role(title, "appTitle")

        if self.content.is_remote:
            source_text = f"Live from GitHub • Content ID: {self.content.content_id}"
        else:
            source_text = "Could not reach GitHub • Live release notes unavailable"

        subtitle = QLabel(source_text, header)
        subtitle.setWordWrap(True)
        set_widget_role(subtitle, "sectionHint")

        header_layout.addWidget(eyebrow)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        root.addWidget(header, 0)

        self.viewer = QTextBrowser(self)
        self.viewer.setObjectName("WhatsNewViewer")
        self.viewer.setOpenExternalLinks(True)
        self.viewer.setReadOnly(True)
        if self.content.format == "html":
            self.viewer.setHtml(self.content.body)
        elif hasattr(self.viewer, "setMarkdown"):
            self.viewer.setMarkdown(self.content.body)
        else:
            self.viewer.setPlainText(self.content.body)
        root.addWidget(self.viewer, 1)

        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 0, 0, 0)
        bottom.setSpacing(10)

        self.suppress_checkbox = QCheckBox("Don’t show this again for this update", self)
        self.suppress_checkbox.setChecked(True)
        self.suppress_checkbox.setVisible(self.allow_suppress)
        bottom.addWidget(self.suppress_checkbox, 1)

        release_notes_btn = QPushButton("Open Release Notes", self)
        release_notes_btn.setCursor(Qt.PointingHandCursor)
        set_widget_role(release_notes_btn, "secondary")
        release_notes_btn.clicked.connect(self._open_release_notes)

        download_btn = QPushButton("Download Latest", self)
        download_btn.setCursor(Qt.PointingHandCursor)
        set_widget_role(download_btn, "accent")
        download_btn.clicked.connect(self._open_download)

        close_btn = QPushButton("Close", self)
        close_btn.setCursor(Qt.PointingHandCursor)
        set_widget_role(close_btn, "secondary")
        close_btn.clicked.connect(self.accept)

        bottom.addWidget(release_notes_btn)
        bottom.addWidget(download_btn)
        bottom.addWidget(close_btn)
        root.addLayout(bottom)

    def should_mark_seen(self) -> bool:
        return self.allow_suppress and self.suppress_checkbox.isChecked()

    def _open_download(self) -> None:
        QDesktopServices.openUrl(QUrl(self.content.download_url))

    def _open_release_notes(self) -> None:
        QDesktopServices.openUrl(QUrl(self.content.release_notes_url))
