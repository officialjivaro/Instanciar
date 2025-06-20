# appdata/gui/main_window.py
import threading, webbrowser
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QMenuBar, QLabel, QHBoxLayout,
    QPushButton, QHeaderView, QApplication
)
from PySide6.QtGui import QPalette, QColor, QIcon, QFont
from PySide6.QtCore import Qt
from appdata.utils.resource_helpers import rp
from appdata.utils.windows_effects import enable_mica
from appdata.gui.widgets.instance_tree import InstanceTree
from appdata.gui.widgets.command_bar import CommandBar
from appdata.gui.widgets.toast import ToastCenter
from appdata.logic.instance_manager import LogicInstanceManager
from appdata.logic.main_window import MainWindowLogic
from appdata.gui.widgets.progress_bar import InstallProgressDialog
from appdata.logic.install import InstallWorker
from appdata.version.version import VERSION
from appdata.logic.adsense import create_adsense_view, load_adsense_content
from appdata.config.style_constants import ACCENT_COLOR, BACKGROUND_MAIN, TEXT_COLOR, GROUP_HOVER, FONT_FAMILY, FONT_SIZE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        QApplication.instance().setFont(QFont(FONT_FAMILY, FONT_SIZE))
        enable_mica(self)
        self.setWindowIcon(QIcon(rp("appdata/media/icon.ico")))
        self.setWindowTitle(f"Instanciar v{VERSION}")
        pal = self.palette()
        pal.setColor(QPalette.Window, QColor(BACKGROUND_MAIN))
        pal.setColor(QPalette.WindowText, QColor(TEXT_COLOR))
        pal.setColor(QPalette.Base, QColor(BACKGROUND_MAIN))
        pal.setColor(QPalette.Button, QColor(BACKGROUND_MAIN))
        pal.setColor(QPalette.ButtonText, QColor(TEXT_COLOR))
        self.setPalette(pal)
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
            """
        )
        self.resize(1000, 562)
        mb = QMenuBar(self)
        self.setMenuBar(mb)
        fmenu = mb.addMenu("File")
        fmenu.addAction("Install", self.on_install)
        fmenu.addAction("Exit", self.close)
        hmenu = mb.addMenu("Help")
        hmenu.addAction("Commands", self.commands_clicked)
        hmenu.addAction("About Jivaro", self.about_clicked)
        hmenu.addAction("Discord", self.discord_clicked)
        hmenu.addAction("Get Proxies", self.proxies_clicked)
        central = QWidget(self)
        central.setObjectName("central")
        lay = QVBoxLayout(central)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(8)
        self.setCentralWidget(central)
        title = QLabel("Instance & Group List", central)
        title.setFont(QFont(FONT_FAMILY, FONT_SIZE + 5, QFont.Bold))
        title.setAlignment(Qt.AlignHCenter)
        lay.addWidget(title)
        self.manager = LogicInstanceManager()
        self.logic = MainWindowLogic(self.manager)
        self.logic.toastRequested.connect(lambda m: ToastCenter().show(m, anchor_widget=self))
        self.tree = InstanceTree(central)
        self.tree.setColumnCount(2)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Interactive)
        lay.addWidget(self.tree)
        self.logic.refresh_tree(self.tree)
        self.command_bar = CommandBar(central)
        lay.addWidget(self.command_bar)
        self.command_bar.setEnabled(False)
        btn_row = QHBoxLayout()
        self.create_instance_btn = QPushButton("Create Instance", central)
        self.create_group_btn = QPushButton("Create Group", central)
        self.up_btn = QPushButton("Move Up", central)
        self.down_btn = QPushButton("Move Down", central)
        btn_row.addWidget(self.create_instance_btn)
        btn_row.addWidget(self.create_group_btn)
        btn_row.addWidget(self.up_btn)
        btn_row.addWidget(self.down_btn)
        lay.addLayout(btn_row)
        self.ad_view = create_adsense_view()
        lay.addWidget(self.ad_view, alignment=Qt.AlignHCenter)
        self.reload_ad()
        self.tree.itemSelectionChanged.connect(self._selection_changed)
        self.command_bar.launchRequested.connect(self._cmd_launch)
        self.command_bar.editRequested.connect(self._cmd_edit)
        self.command_bar.deleteRequested.connect(self._cmd_delete)
        self.command_bar.duplicateRequested.connect(self._cmd_duplicate)
        self.create_instance_btn.clicked.connect(lambda: self.logic.create_new_instance(self))
        self.create_group_btn.clicked.connect(lambda: self.logic.create_new_group(self))
        self.up_btn.clicked.connect(lambda: self.logic.move_selected_up(self.tree))
        self.down_btn.clicked.connect(lambda: self.logic.move_selected_down(self.tree))

    def _selection_changed(self):
        self.command_bar.setEnabled(bool(self.tree.selectedItems()))

    def _cmd_launch(self):
        self.logic.launch_selected(self.tree)

    def _cmd_edit(self):
        self.logic.edit_selected(self.tree, self)

    def _cmd_delete(self):
        self.logic.delete_selected(self.tree)

    def _cmd_duplicate(self):
        self.logic.duplicate_selected(self.tree)

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
        wk = InstallWorker()
        wk.progress_signal.connect(dlg.update_progress)
        wk.finished_signal.connect(lambda: (dlg.close(), ToastCenter().show("Installed successfully!", anchor_widget=self)))
        threading.Thread(target=wk.run_install, daemon=True).start()
        dlg.exec()

    def reload_ad(self):
        load_adsense_content(self.ad_view)
