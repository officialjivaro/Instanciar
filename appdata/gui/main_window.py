# appdata/gui/main_window.py
import threading
import webbrowser

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from appdata.config.style_constants import FONT_FAMILY, FONT_SIZE
from appdata.gui.themes.app_theme import apply_app_theme, set_widget_role
from appdata.gui.whats_new_dialog import WhatsNewDialog
from appdata.gui.widgets.command_bar import CommandBar
from appdata.gui.widgets.dashboard_filter_bar import DashboardFilterBar
from appdata.gui.widgets.instance_tree import InstanceTree
from appdata.gui.widgets.progress_bar import InstallProgressDialog
from appdata.gui.widgets.selection_details_panel import SelectionDetailsPanel
from appdata.gui.widgets.toast import ToastCenter
from appdata.logic.install import InstallWorker
from appdata.logic.instance_manager import LogicInstanceManager
from appdata.logic.main_window import MainWindowLogic
from appdata.logic.whats_new_service import (
    has_seen_content,
    load_whats_new_content,
    mark_content_seen,
)
from appdata.utils.resource_helpers import rp
from appdata.utils.windows_effects import enable_mica
from appdata.version.version import VERSION


DONATE_URL = "https://jivaro.net/about/donate"


class MainWindow(QMainWindow):
    """Main dashboard for browsing, inspecting, and launching instances."""

    whatsNewReady = Signal(object, bool)

    def __init__(self):
        super().__init__()
        QApplication.instance().setFont(QFont(FONT_FAMILY, FONT_SIZE))
        apply_app_theme(self)
        enable_mica(self)

        self.setWindowIcon(QIcon(rp("appdata/media/icon.ico")))
        self.setWindowTitle(f"Instanciar v{VERSION}")
        self.resize(1366, 768)
        # Keep a true 16:9 dashboard baseline. Below this size the app
        # would have to hide or scroll controls, so we prevent that instead.
        self.setMinimumSize(1280, 720)
        self.setBaseSize(1280, 720)
        self._compact_mode = False
        self._filter_text = ""
        self._issues_only = False

        self.manager = LogicInstanceManager()
        self.logic = MainWindowLogic(self.manager)
        self.logic.toastRequested.connect(self._show_toast, Qt.ConnectionType.QueuedConnection)
        self.whatsNewReady.connect(self._open_whats_new_payload, Qt.ConnectionType.QueuedConnection)

        self._build_menu()
        self._build_ui()
        self._connect_signals()

        self._refresh_tree(preserve_selection=False)
        self._refresh_dashboard_summary()
        self._refresh_selection_ui()
        self._sync_responsive_layout()

    def _build_menu(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        file_menu = menu_bar.addMenu("File")
        file_menu.addAction("Install", self.on_install)
        file_menu.addAction("Exit", self.close)

        help_menu = menu_bar.addMenu("Help")
        help_menu.addAction("What’s New", lambda: self.show_whats_new(force=True))
        help_menu.addSeparator()
        help_menu.addAction("About Instanciar", self.commands_clicked)
        help_menu.addAction("About Jivaro", self.about_clicked)
        help_menu.addAction("Join Discord", self.discord_clicked)
        help_menu.addAction("Get Proxies", self.proxies_clicked)
        help_menu.addSeparator()
        help_menu.addAction("Donate", self.donate_clicked)

    def _build_ui(self):
        central = QWidget(self)
        central.setObjectName("MainCentralWidget")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self.shell_splitter = QSplitter(Qt.Horizontal, central)
        self.shell_splitter.setChildrenCollapsible(False)
        self.shell_splitter.setHandleWidth(6)
        self.shell_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.sidebar = self._build_sidebar()
        self.workspace = self._build_workspace()

        self.shell_splitter.addWidget(self.sidebar)
        self.shell_splitter.addWidget(self.workspace)
        self.shell_splitter.setStretchFactor(0, 0)
        self.shell_splitter.setStretchFactor(1, 1)
        self.shell_splitter.setSizes([286, 970])

        root.addWidget(self.shell_splitter)

    def _build_sidebar(self):
        sidebar = QFrame(self)
        sidebar.setObjectName("DashboardSidebar")
        sidebar.setMinimumWidth(280)
        sidebar.setMaximumWidth(330)
        sidebar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        brand = QFrame(sidebar)
        brand.setObjectName("SidebarBrandCard")
        brand.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(12, 10, 12, 10)
        brand_layout.setSpacing(3)

        eyebrow = QLabel("Browser Workspace", brand)
        set_widget_role(eyebrow, "eyebrow")

        title = QLabel("Instanciar", brand)
        title.setWordWrap(True)
        set_widget_role(title, "appTitle")

        version = QLabel(f"v{VERSION}", brand)
        set_widget_role(version, "sectionHint")

        subtitle = QLabel(
            "Create Chrome workspaces, keep profiles organized, and spot setup issues before launch.",
            brand,
        )
        subtitle.setWordWrap(True)
        subtitle.setMaximumHeight(58)
        set_widget_role(subtitle, "appSubtitle")

        brand_layout.addWidget(eyebrow)
        brand_layout.addWidget(title)
        brand_layout.addWidget(version)
        brand_layout.addWidget(subtitle)
        layout.addWidget(brand, 0)

        stats_frame = QFrame(sidebar)
        stats_frame.setObjectName("SidebarStatCard")
        stats_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(10, 8, 10, 8)
        stats_layout.setSpacing(5)

        self.groups_stat = self._make_stat_pair("Groups", "0", stats_frame)
        self.instances_stat = self._make_stat_pair("Instances", "0", stats_frame)
        self.issues_stat = self._make_stat_pair("Setup Issues", "0", stats_frame)
        stats_layout.addLayout(self.groups_stat["layout"])
        stats_layout.addLayout(self.instances_stat["layout"])
        stats_layout.addLayout(self.issues_stat["layout"])
        layout.addWidget(stats_frame, 0)

        self.command_bar = CommandBar(sidebar)
        self.command_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        layout.addWidget(self.command_bar, 0)

        layout.addStretch(1)

        support = QFrame(sidebar)
        support.setObjectName("SidebarSupportCard")
        support.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        support_layout = QVBoxLayout(support)
        support_layout.setContentsMargins(10, 8, 10, 8)
        support_layout.setSpacing(6)

        donate_note = QLabel("Support development and updates.", support)
        donate_note.setWordWrap(True)
        donate_note.setMaximumHeight(36)
        set_widget_role(donate_note, "sectionHint")

        self.donate_btn = QPushButton("Donate", support)
        self.donate_btn.setCursor(Qt.PointingHandCursor)
        set_widget_role(self.donate_btn, "donate")
        self.donate_btn.clicked.connect(self.donate_clicked)

        support_layout.addWidget(donate_note)
        support_layout.addWidget(self.donate_btn)
        layout.addWidget(support, 0)
        return sidebar

    def _make_stat_pair(self, label_text, value_text, parent):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        label = QLabel(label_text, parent)
        set_widget_role(label, "statLabel")

        value = QLabel(value_text, parent)
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        set_widget_role(value, "statNumber")

        row.addWidget(label, 1)
        row.addWidget(value, 0)
        return {"layout": row, "label": label, "value": value}

    def _build_workspace(self):
        workspace = QWidget(self)
        workspace.setObjectName("WorkspacePanel")
        workspace.setMinimumWidth(880)
        workspace.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addWidget(self._build_workspace_header(), 0)

        self.filter_bar = DashboardFilterBar(workspace)
        layout.addWidget(self.filter_bar, 0)

        self.content_splitter = QSplitter(Qt.Horizontal, workspace)
        self.content_splitter.setChildrenCollapsible(False)
        self.content_splitter.setHandleWidth(6)
        self.content_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        tree_card = QFrame(self.content_splitter)
        tree_card.setObjectName("TreeWorkspaceCard")
        tree_card.setMinimumWidth(540)
        tree_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tree_layout = QVBoxLayout(tree_card)
        tree_layout.setContentsMargins(9, 9, 9, 9)
        tree_layout.setSpacing(6)

        tree_title = QLabel("Instances & Groups", tree_card)
        set_widget_role(tree_title, "sectionTitle")
        tree_hint = QLabel("Select an item to inspect it. Right-click the tree for context actions.", tree_card)
        tree_hint.setWordWrap(True)
        set_widget_role(tree_hint, "sectionHint")

        self.tree = InstanceTree(tree_card)
        self.tree.setColumnCount(2)
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)

        tree_layout.addWidget(tree_title, 0)
        tree_layout.addWidget(tree_hint, 0)
        tree_layout.addWidget(self.tree, 1)

        self.details_panel = SelectionDetailsPanel(self.content_splitter)

        self.content_splitter.addWidget(tree_card)
        self.content_splitter.addWidget(self.details_panel)
        self.content_splitter.setStretchFactor(0, 7)
        self.content_splitter.setStretchFactor(1, 3)
        self.content_splitter.setSizes([720, 340])

        layout.addWidget(self.content_splitter, 1)
        return workspace

    def _build_workspace_header(self):
        header = QFrame(self)
        header.setObjectName("WorkspaceTopCard")
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        text_area = QVBoxLayout()
        text_area.setContentsMargins(0, 0, 0, 0)
        text_area.setSpacing(3)

        title = QLabel("Dashboard", header)
        title.setWordWrap(True)
        set_widget_role(title, "appTitle")
        subtitle = QLabel("Search, review setup health, and launch the right browser profile quickly.", header)
        subtitle.setWordWrap(True)
        subtitle.setMaximumHeight(58)
        set_widget_role(subtitle, "appSubtitle")

        text_area.addWidget(title)
        text_area.addWidget(subtitle)

        self.header_issue_label = QLabel("No setup issues", header)
        self.header_issue_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.header_issue_label.setMinimumWidth(120)
        set_widget_role(self.header_issue_label, "sectionHint")

        layout.addLayout(text_area, 1)
        layout.addWidget(self.header_issue_label, 0)
        return header

    def _connect_signals(self):
        self.tree.itemSelectionChanged.connect(self._selection_changed)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_tree_context_menu)

        self.filter_bar.searchChanged.connect(self._on_filter_changed)
        self.filter_bar.issuesOnlyChanged.connect(self._on_issues_only_changed)

        self.command_bar.createInstanceRequested.connect(self._create_instance)
        self.command_bar.createGroupRequested.connect(self._create_group)
        self.command_bar.launchRequested.connect(self._cmd_launch)
        self.command_bar.editRequested.connect(self._cmd_edit)
        self.command_bar.deleteRequested.connect(self._cmd_delete)
        self.command_bar.duplicateRequested.connect(self._cmd_duplicate)
        self.command_bar.moveUpRequested.connect(self._move_selected_up)
        self.command_bar.moveDownRequested.connect(self._move_selected_down)

        self.manager.proxyTested.connect(lambda *_: self._refresh_after_data_change())
        self.manager.statusChanged.connect(self._refresh_after_data_change)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_responsive_layout()

    def _sync_responsive_layout(self):
        """Resize the dashboard proportionally inside the 16:9 minimum window.

        The app has a real minimum size instead of adding layout scrollbars.
        Above that minimum, splitter sections scale smoothly with the window.
        """
        if not hasattr(self, "content_splitter"):
            return

        total_width = max(1280, self.width())
        sidebar_width = min(320, max(270, int(total_width * 0.22)))
        workspace_width = max(880, total_width - sidebar_width - 40)
        self.shell_splitter.setSizes([sidebar_width, workspace_width])

        available_w = max(860, self.content_splitter.width())
        details_w = min(430, max(320, int(available_w * 0.30)))
        tree_w = max(540, available_w - details_w)
        self.content_splitter.setOrientation(Qt.Horizontal)
        self.content_splitter.setSizes([tree_w, details_w])

    @Slot(str, str)
    def _show_toast(self, message, kind="info"):
        ToastCenter().show(message, anchor_widget=self, kind=kind)

    def _selected_identity(self):
        item = self.tree.currentItem()
        if item is None:
            return None, None
        info = item.data(0, Qt.UserRole) or {}
        return info.get("name"), info.get("type")

    def _refresh_tree(self, preserve_selection=True):
        selected_name, selected_type = self._selected_identity() if preserve_selection else (None, None)
        self.logic.refresh_tree(self.tree, search_text=self._filter_text, issues_only=self._issues_only)
        filtered = bool(self._filter_text or self._issues_only)
        self.tree.setDragEnabled(not filtered)
        if selected_name and selected_type:
            self.logic._reselect(self.tree, selected_name, selected_type)

    def _refresh_dashboard_summary(self):
        summary = self.logic.get_dashboard_summary()
        self.groups_stat["value"].setText(str(summary["groups"]))
        self.instances_stat["value"].setText(str(summary["instances"]))
        self.issues_stat["value"].setText(str(summary["issues"]))
        self.filter_bar.set_summary(summary["groups"], summary["instances"], summary["issues"])
        issue_word = "issue" if summary["issues"] == 1 else "issues"
        self.header_issue_label.setText(f'{summary["issues"]} setup {issue_word}')

    def _refresh_selection_ui(self):
        states = self.logic.get_action_states(self.tree)
        if self._filter_text or self._issues_only:
            # Moving items while the tree is filtered can confuse ordering, so keep ordering disabled until filters are cleared.
            states["move_up"] = False
            states["move_down"] = False
        self.command_bar.set_actions_enabled(states)
        self.details_panel.update_details(self.logic.get_selection_details(self.tree))

    def _refresh_after_data_change(self):
        self._refresh_tree(preserve_selection=True)
        self._refresh_dashboard_summary()
        self._refresh_selection_ui()

    def _selection_changed(self):
        self._refresh_selection_ui()

    def _on_filter_changed(self, text):
        self._filter_text = str(text or "").strip()
        self._refresh_tree(preserve_selection=True)
        self._refresh_selection_ui()

    def _on_issues_only_changed(self, checked):
        self._issues_only = bool(checked)
        self._refresh_tree(preserve_selection=True)
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
        self._refresh_after_data_change()

    def _cmd_delete(self):
        self.logic.delete_selected(self.tree)
        self._refresh_after_data_change()

    def _cmd_duplicate(self):
        self.logic.duplicate_selected(self.tree)
        self._refresh_after_data_change()

    def _create_instance(self):
        self.logic.create_new_instance(self)
        self._refresh_after_data_change()

    def _create_group(self):
        self.logic.create_new_group(self)
        self._refresh_after_data_change()

    def _move_selected_up(self):
        self.logic.move_selected_up(self.tree)
        self._refresh_after_data_change()

    def _move_selected_down(self):
        self.logic.move_selected_down(self.tree)
        self._refresh_after_data_change()

    def show_whats_new_if_needed(self):
        """Show live release notes once per new GitHub content ID.

        If GitHub cannot be reached, show the unavailable panel instead of
        reading bundled release notes from the app.
        """
        self.show_whats_new(force=False)

    def show_whats_new(self, *, force=False):
        """Load the live What's New content and open the panel when needed."""
        threading.Thread(
            target=self._load_whats_new_worker,
            args=(bool(force),),
            daemon=True,
        ).start()

    def _load_whats_new_worker(self, force):
        content = load_whats_new_content(prefer_remote=True)
        self.whatsNewReady.emit(content, bool(force))

    @Slot(object, bool)
    def _open_whats_new_payload(self, content, force=False):
        # Seen-state only applies to successfully loaded GitHub content.
        # If GitHub is unreachable, show the error panel and do not mark it seen.
        if content.is_remote and not force and has_seen_content(content.content_id):
            return

        dialog = WhatsNewDialog(content, self, allow_suppress=(not force and content.is_remote))
        dialog.exec()

        if content.is_remote and dialog.should_mark_seen():
            mark_content_seen(content.content_id)

    def commands_clicked(self):
        self.logic.open_commands()

    def about_clicked(self):
        self.logic.open_about_jivaro()

    def discord_clicked(self):
        self.logic.open_discord()

    def proxies_clicked(self):
        self.logic.open_proxies()

    def donate_clicked(self):
        webbrowser.open(DONATE_URL)

    def on_install(self):
        dlg = InstallProgressDialog(self)
        worker = InstallWorker()
        worker.progress_signal.connect(dlg.update_progress)
        worker.finished_signal.connect(dlg.close)
        worker.succeeded_signal.connect(lambda: self._show_toast("Instanciar installed successfully.", "success"))
        worker.failed_signal.connect(lambda message: self._show_toast(f"Install failed: {message}", "error"))

        threading.Thread(target=worker.run_install, daemon=True).start()
        dlg.exec()
