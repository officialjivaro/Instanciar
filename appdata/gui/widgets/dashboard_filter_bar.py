# appdata/gui/widgets/dashboard_filter_bar.py
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QFrame, QGridLayout, QLabel, QLineEdit, QSizePolicy

from appdata.gui.themes.app_theme import set_widget_role


class DashboardFilterBar(QFrame):
    """Search and setup-issue filters for the main dashboard.

    The layout switches between one row and two rows so the search box does not
    crush the checkbox/summary text when the app is resized narrower.
    """

    searchChanged = Signal(str)
    issuesOnlyChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DashboardFilterBar")
        self._compact = None

        self.layout_grid = QGridLayout(self)
        self.layout_grid.setContentsMargins(12, 10, 12, 10)
        self.layout_grid.setHorizontalSpacing(10)
        self.layout_grid.setVerticalSpacing(8)

        self.label = QLabel("Find", self)
        set_widget_role(self.label, "sectionTitle")

        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("Search instances, groups, region, proxy status...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setMinimumWidth(180)
        self.search_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.issues_only_cb = QCheckBox("Show setup issues only", self)
        self.issues_only_cb.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

        self.summary_label = QLabel("0 groups • 0 instances • 0 issues", self)
        self.summary_label.setWordWrap(False)
        self.summary_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        set_widget_role(self.summary_label, "sectionHint")

        self._apply_layout(compact=False)

        self.search_edit.textChanged.connect(self.searchChanged.emit)
        self.issues_only_cb.toggled.connect(self.issuesOnlyChanged.emit)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_layout(compact=self.width() < 760)

    def _clear_grid(self) -> None:
        for widget in (self.label, self.search_edit, self.issues_only_cb, self.summary_label):
            self.layout_grid.removeWidget(widget)

    def _apply_layout(self, compact: bool) -> None:
        if compact == self._compact:
            return
        self._compact = compact
        self._clear_grid()

        if compact:
            self.layout_grid.addWidget(self.label, 0, 0)
            self.layout_grid.addWidget(self.search_edit, 0, 1, 1, 3)
            self.layout_grid.addWidget(self.issues_only_cb, 1, 1, 1, 2)
            self.layout_grid.addWidget(self.summary_label, 1, 3)
            self.layout_grid.setColumnStretch(0, 0)
            self.layout_grid.setColumnStretch(1, 1)
            self.layout_grid.setColumnStretch(2, 0)
            self.layout_grid.setColumnStretch(3, 0)
        else:
            self.layout_grid.addWidget(self.label, 0, 0)
            self.layout_grid.addWidget(self.search_edit, 0, 1)
            self.layout_grid.addWidget(self.issues_only_cb, 0, 2)
            self.layout_grid.addWidget(self.summary_label, 0, 3)
            self.layout_grid.setColumnStretch(0, 0)
            self.layout_grid.setColumnStretch(1, 1)
            self.layout_grid.setColumnStretch(2, 0)
            self.layout_grid.setColumnStretch(3, 0)

    def search_text(self) -> str:
        return self.search_edit.text().strip()

    def issues_only(self) -> bool:
        return self.issues_only_cb.isChecked()

    def set_summary(self, groups: int, instances: int, issues: int) -> None:
        issue_word = "issue" if int(issues) == 1 else "issues"
        self.summary_label.setText(f"{int(groups)} groups • {int(instances)} instances • {int(issues)} {issue_word}")
