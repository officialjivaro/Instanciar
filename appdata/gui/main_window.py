# appdata/gui/main_window.py
import threading

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QMenuBar,
    QLabel,
    QHeaderView,
    QApplication,
    QSplitter,
    QMenu,
)
from PySide6.QtGui import QPalette, QColor, QIcon, QFont
from PySide6.QtCore import Qt, Slot

from appdata.utils.resource_helpers import rp
from appdata.utils.windows_effects import enable_mica
from appdata.gui.widgets.instance_tree import InstanceTree
from appdata.gui.widgets.command_bar import CommandBar
from appdata.gui.widgets.selection_details_panel import SelectionDetailsPanel
from appdata.gui.widgets.toast import ToastCenter
from appdata.logic.instance_manager import LogicInstanceManager
from appdata.logic.main_window import MainWindowLogic
from appdata.gui.widgets.progress_bar import InstallProgressDialog
from appdata.logic.install import InstallWorker
from appdata.version.version import VERSION
from appdata.config.style_constants import ACCENT_COLOR, BACKGROUND_MAIN, TEXT_COLOR, GROUP_HOVER, FONT_FAMILY, FONT_SIZE


class MainWindow(QMainWindow):
    """Main application window showing the instance/group list and controls."""

    def __init__(self):
        super().__init__()
        QApplication.instance().setFont(QFont(FONT_FAMILY, FONT_SIZE))
        enable_mica(self)
        self.setWindowIcon(QIcon(rp("appdata/media/icon.ico")))
        self.setWindowTitle(f"Instanciar v{VERSION}")

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(BACKGROUND_MAIN))
        palette.setColor(QPalette.WindowText, QColor(TEXT_COLOR))
        palette.setColor(QPalette.Base, QColor(BACKGROUND_MAIN))
        palette.setColor(QPalette.Button, QColor(BACKGROUND_MAIN))
        palette.setColor(QPalette.ButtonText, QColor(TEXT_COLOR))
        self.setPalette(palette)

        self.setStyleSheet(
            f"""
            QMainWindow{{background:{BACKGROUND_MAIN};}}
            QWidget#central{{background:{BACKGROUND_MAIN};}}
            QMenuBar{{background:{BACKGROUND_MAIN};color:{TEXT_COLOR};}}
            QMenuBar::item:selected{{background:{GROUP_HOVER};}}
            QMenu{{background:{BACKGROUND_MAIN};color:{TEXT_COLOR};}}
            QMenu::item:selected{{background:{GROUP_HOVER};}}
            QTreeWidget{{outline:0;border:none;background:{BACKGROUND_MAIN};}}
            QTreeWidget::item:hover{{background:{GROUP_HOVER};}}
            QTreeWidget::item:selected{{background:{ACCENT_COLOR};}}
            QPushButton{{background:{BACKGROUND_MAIN};color:{TEXT_COLOR};
                         border:1px solid {GROUP_HOVER};border-radius:4px;padding:4px 10px;}}
            QPushButton:hover{{background:{GROUP_HOVER};}}
            QSplitter::handle{{background:{GROUP_HOVER};}}
            """
        )

        self.resize(1120, 620)

        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction("Install", self.on_install)
        file_menu.addAction("Exit", self.close)

        help_menu = menu_bar.addMenu("Help")
        help_menu.addAction("About Instanciar", self.commands_clicked)
        help_menu.addAction("About Jivaro", self.about_clicked)
        help_menu.addAction("Join Discord", self.discord_clicked)
        help_menu.addAction("Get Proxies", self.proxies_clicked)

        central = QWidget(self)
        central.setObjectName("central")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        self.setCentralWidget(central)

        title = QLabel("Instance & Group List", central)
        title.setFont(QFont(FONT_FAMILY, FONT_SIZE + 5, QFont.Bold))
        title.setAlignment(Qt.AlignHCenter)
        layout.addWidget(title)

        self.manager = LogicInstanceManager()
        self.logic = MainWindowLogic(self.manager)
        self.logic.toastRequested.connect(self._show_toast, Qt.ConnectionType.QueuedConnection)

        self.command_bar = CommandBar(central)
        layout.addWidget(self.command_bar)

        self.splitter = QSplitter(Qt.Horizontal, central)
        self.splitter.setChildrenCollapsible(False)

        self.tree = InstanceTree(self.splitter)
        self.tree.setColumnCount(2)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Interactive)

        self.details_panel = SelectionDetailsPanel(self.splitter)

        self.splitter.addWidget(self.tree)
        self.splitter.addWidget(self.details_panel)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setSizes([760, 320])

        layout.addWidget(self.splitter, 1)

        self.logic.refresh_tree(self.tree)

        self.tree.itemSelectionChanged.connect(self._selection_changed)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_tree_context_menu)

        self.command_bar.createInstanceRequested.connect(self._create_instance)
        self.command_bar.createGroupRequested.connect(self._create_group)
        self.command_bar.launchRequested.connect(self._cmd_launch)
        self.command_bar.editRequested.connect(self._cmd_edit)
        self.command_bar.deleteRequested.connect(self._cmd_delete)
        self.command_bar.duplicateRequested.connect(self._cmd_duplicate)
        self.command_bar.moveUpRequested.connect(self._move_selected_up)
        self.command_bar.moveDownRequested.connect(self._move_selected_down)

        self.manager.proxyTested.connect(lambda *_: self._refresh_selection_ui())
        self.manager.statusChanged.connect(self._refresh_selection_ui)

        self._refresh_selection_ui()

    @Slot(str, str)
    def _show_toast(self, message, kind="info"):
        """Display toast messages on the GUI thread."""
        ToastCenter().show(message, anchor_widget=self, kind=kind)

    def _refresh_selection_ui(self):
        states = self.logic.get_action_states(self.tree)
        self.command_bar.set_actions_enabled(states)
        self.details_panel.update_details(self.logic.get_selection_details(self.tree))

    def _selection_changed(self):
        self._refresh_selection_ui()

    def _add_context_action(self, menu, text, callback, enabled=True):
        action = menu.addAction(text)
        action.setEnabled(bool(enabled))
        if enabled:
            action.triggered.connect(callback)
        return action

    def _show_tree_context_menu(self, pos):
        menu = QMenu(self)
        item = self.tree.itemAt(pos)

        if item is None:
            self._add_context_action(menu, "Create Instance", self._create_instance, True)
            self._add_context_action(menu, "Create Group", self._create_group, True)
            menu.exec(self.tree.viewport().mapToGlobal(pos))
            return

        self.tree.setCurrentItem(item)
        self._refresh_selection_ui()

        info = item.data(0, Qt.UserRole) or {}
        states = self.logic.get_action_states(self.tree)

        if info.get("type") == "group":
            self._add_context_action(menu, "Edit Group", self._cmd_edit, states.get("edit", False))
            self._add_context_action(menu, "Delete Group", self._cmd_delete, states.get("delete", False))
            menu.addSeparator()
            self._add_context_action(menu, "Move Group Up", self._move_selected_up, states.get("move_up", False))
            self._add_context_action(menu, "Move Group Down", self._move_selected_down, states.get("move_down", False))
        else:
            self._add_context_action(menu, "Launch Instance", self._cmd_launch, states.get("launch", False))
            self._add_context_action(menu, "Edit Instance", self._cmd_edit, states.get("edit", False))
            self._add_context_action(menu, "Duplicate Instance", self._cmd_duplicate, states.get("duplicate", False))
            self._add_context_action(menu, "Delete Instance", self._cmd_delete, states.get("delete", False))
            menu.addSeparator()
            self._add_context_action(menu, "Move Instance Up", self._move_selected_up, states.get("move_up", False))
            self._add_context_action(menu, "Move Instance Down", self._move_selected_down, states.get("move_down", False))

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _cmd_launch(self):
        self.logic.launch_selected(self.tree)
        self._refresh_selection_ui()

    def _cmd_edit(self):
        self.logic.edit_selected(self.tree, self)
        self._refresh_selection_ui()

    def _cmd_delete(self):
        self.logic.delete_selected(self.tree)
        self._refresh_selection_ui()

    def _cmd_duplicate(self):
        self.logic.duplicate_selected(self.tree)
        self._refresh_selection_ui()

    def _create_instance(self):
        self.logic.create_new_instance(self)
        self._refresh_selection_ui()

    def _create_group(self):
        self.logic.create_new_group(self)
        self._refresh_selection_ui()

    def _move_selected_up(self):
        self.logic.move_selected_up(self.tree)
        self._refresh_selection_ui()

    def _move_selected_down(self):
        self.logic.move_selected_down(self.tree)
        self._refresh_selection_ui()

    def commands_clicked(self):
        self.logic.open_commands()

    def about_clicked(self):
        self.logic.open_about_jivaro()

    def discord_clicked(self):
        self.logic.open_discord()

    def proxies_clicked(self):
        self.logic.open_proxies()

    def on_install(self):
        dlg = InstallProgressDialog(self)
        worker = InstallWorker()
        worker.progress_signal.connect(dlg.update_progress)
        worker.finished_signal.connect(dlg.close)
        worker.succeeded_signal.connect(lambda: self._show_toast("Instanciar installed successfully.", "success"))
        worker.failed_signal.connect(lambda message: self._show_toast(f"Install failed: {message}", "error"))

        threading.Thread(target=worker.run_install, daemon=True).start()
        dlg.exec()