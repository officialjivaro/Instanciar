# appdata/gui/widgets/command_bar.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFrame
from PySide6.QtCore import Signal


class CommandBar(QWidget):
    """Unified action strip for creation, item actions, and movement."""

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
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._buttons = {}

        self._add_button(layout, "create_instance", "Create Instance", self.createInstanceRequested)
        self._add_button(layout, "create_group", "Create Group", self.createGroupRequested)
        self._add_separator(layout)
        self._add_button(layout, "launch", "Launch", self.launchRequested)
        self._add_button(layout, "edit", "Edit", self.editRequested)
        self._add_button(layout, "duplicate", "Duplicate", self.duplicateRequested)
        self._add_button(layout, "delete", "Delete", self.deleteRequested)
        self._add_separator(layout)
        self._add_button(layout, "move_up", "Move Up", self.moveUpRequested)
        self._add_button(layout, "move_down", "Move Down", self.moveDownRequested)
        layout.addStretch(1)

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

    def _add_button(self, layout, action, text, signal):
        btn = QPushButton(text, self)
        btn.setMinimumHeight(32)
        btn.clicked.connect(signal.emit)
        layout.addWidget(btn)
        self._buttons[action] = btn

    def _add_separator(self, layout):
        sep = QFrame(self)
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

    def set_action_enabled(self, action, enabled):
        """Enable or disable a single action button."""
        btn = self._buttons.get(action)
        if btn is not None:
            btn.setEnabled(bool(enabled))

    def set_actions_enabled(self, states):
        """Apply a batch of enabled/disabled states to all known action buttons."""
        for action, enabled in states.items():
            if action in self._buttons:
                self._buttons[action].setEnabled(bool(enabled))