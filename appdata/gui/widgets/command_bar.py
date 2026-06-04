# appdata/gui/widgets/command_bar.py
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout

from appdata.gui.themes.app_theme import set_widget_role


class CommandBar(QFrame):
    """Compact dashboard action dock.

    This version is designed to fit inside the fixed 16:9 dashboard minimum size
    without using a scroll area. It keeps the same signals as the old command bar.
    """

    createInstanceRequested = Signal()
    createGroupRequested = Signal()
    launchRequested = Signal()
    editRequested = Signal()
    deleteRequested = Signal()
    duplicateRequested = Signal()
    moveUpRequested = Signal()
    moveDownRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CommandBarCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        self._buttons = {}
        self._add_section(
            root,
            "Create",
            (
                ("create_instance", "Create Instance", self.createInstanceRequested, "primary"),
                ("create_group", "Create Group", self.createGroupRequested, "secondary"),
            ),
        )
        self._add_section(
            root,
            "Selected Item",
            (
                ("launch", "Launch", self.launchRequested, "accent"),
                ("edit", "Edit", self.editRequested, "secondary"),
                ("duplicate", "Duplicate", self.duplicateRequested, "secondary"),
                ("delete", "Delete", self.deleteRequested, "danger"),
            ),
        )
        self._add_section(
            root,
            "Order",
            (
                ("move_up", "Move Up", self.moveUpRequested, "muted"),
                ("move_down", "Move Down", self.moveDownRequested, "muted"),
            ),
        )

        self.set_actions_enabled(
            {
                "create_instance": True,
                "create_group": True,
                "launch": False,
                "edit": False,
                "delete": False,
                "duplicate": False,
                "move_up": False,
                "move_down": False,
            }
        )

    def _add_section(self, parent_layout, title: str, button_specs) -> None:
        section = QFrame(self)
        section.setObjectName("CommandSection")
        section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        layout = QVBoxLayout(section)
        layout.setContentsMargins(7, 7, 7, 7)
        layout.setSpacing(4)

        title_label = QLabel(title, section)
        title_label.setWordWrap(False)
        set_widget_role(title_label, "compactSectionTitle")
        layout.addWidget(title_label)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        for index, (action, text, signal, role) in enumerate(button_specs):
            btn = QPushButton(text, section)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(28)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.clicked.connect(signal.emit)
            set_widget_role(btn, role)
            grid.addWidget(btn, index // 2, index % 2)
            self._buttons[action] = btn

        layout.addLayout(grid)
        parent_layout.addWidget(section)

    def set_action_enabled(self, action, enabled):
        btn = self._buttons.get(action)
        if btn is not None:
            btn.setEnabled(bool(enabled))

    def set_actions_enabled(self, states):
        for action, enabled in states.items():
            if action in self._buttons:
                self._buttons[action].setEnabled(bool(enabled))
