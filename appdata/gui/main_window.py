# gui/main_window.py
import os
import sys
import threading
import platform
import random
import webbrowser
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QAbstractItemView,
    QMenuBar,
    QLabel
)
from PySide6.QtGui import (
    QPalette,
    QColor,
    QDesktopServices,
    QIcon,
    QAction 
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage

from appdata.logic.instance_manager import LogicInstanceManager
from appdata.logic.main_window import MainWindowLogic
from appdata.logic.install import InstallWorker
from appdata.gui.progress_bar import InstallProgressDialog
from appdata.version.version import VERSION

def rp(x):
    if hasattr(sys, '_MEIPASS'):
        base = sys._MEIPASS
    else:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base, x)

def get_system_or_random_ua():
    sys_os = platform.system().lower()
    windows_ua = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/113.0.5672.63",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/112.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edg/113.0.1774.35",
    ]
    mac_ua = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/605.1.15 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) Chrome/112.0.5615.137",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) Firefox/112.0",
    ]
    linux_ua = [
        "Mozilla/5.0 (X11; Linux x86_64) Chrome/113.0.5672.63",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) Firefox/111.0",
        "Mozilla/5.0 (X11; Linux x86_64) Edg/112.0.1722.39",
    ]
    fallback_ua = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1) AppleWebKit/605.1.15 Safari/605.1.15",
        "Mozilla/5.0 (Linux; Android 11) Chrome/112.0.5615.136",
        "Mozilla/5.0 (iPad; CPU OS 15_4 like Mac OS X) AppleWebKit/605.1.15 Safari/605.1.15",
    ]

    if "windows" in sys_os:
        return random.choice(windows_ua)
    elif "darwin" in sys_os or "mac" in sys_os:
        return random.choice(mac_ua)
    elif "linux" in sys_os:
        return random.choice(linux_ua)
    else:
        return random.choice(fallback_ua)

class ExternalLinkPage(QWebEnginePage):
    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        if nav_type == QWebEnginePage.NavigationTypeLinkClicked:
            QDesktopServices.openUrl(url)
            return False
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        icon_path = rp("appdata/media/icon.ico")
        self.setWindowIcon(QIcon(icon_path))

        self.setWindowTitle(f"Instanciar v{VERSION}")

        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(50, 50, 50))
        pal.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
        self.setPalette(pal)
        self.resize(400, 400)

        menubar = QMenuBar(self)
        menubar.setStyleSheet(
            "QMenuBar { background-color: rgb(50, 50, 50); color: rgb(220,220,220); }"
            "QMenuBar::item:selected { background-color: rgb(70,70,70); }"
            "QMenu { background-color: rgb(50,50,50); color: rgb(220,220,220); }"
            "QMenu::item:selected { background-color: rgb(70,70,70); }"
        )
        self.setMenuBar(menubar)

        file_menu = menubar.addMenu("File")
        install_action = QAction("Install", self)
        install_action.triggered.connect(self.on_install)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(install_action)
        file_menu.addAction(exit_action)

        help_menu = menubar.addMenu("Help")
        commands_action = QAction("Commands", self)
        commands_action.triggered.connect(self.commands_clicked)
        about_action = QAction("About Jivaro", self)
        about_action.triggered.connect(self.about_clicked)
        discord_action = QAction("Discord", self)
        discord_action.triggered.connect(self.discord_clicked)
        proxies_action = QAction("Get Proxies", self)
        proxies_action.triggered.connect(self.proxies_clicked)
        help_menu.addAction(commands_action)
        help_menu.addAction(about_action)
        help_menu.addAction(discord_action)
        help_menu.addAction(proxies_action)

        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout()
        container.setLayout(layout)
        top_label = QLabel("Instance List")
        top_label.setAlignment(Qt.AlignHCenter)
        layout.addWidget(top_label)

        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        layout.addWidget(self.list_widget)

        btns = QHBoxLayout()
        self.create_button = QPushButton("Create")
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")
        self.launch_button = QPushButton("Launch")
        btns.addWidget(self.create_button)
        btns.addWidget(self.edit_button)
        btns.addWidget(self.delete_button)
        btns.addWidget(self.launch_button)
        layout.addLayout(btns)

        self.manager = LogicInstanceManager()
        self.logic = MainWindowLogic(self.manager)
        self.logic.refresh_list(self.list_widget)

        self.create_button.clicked.connect(self.on_create)
        self.edit_button.clicked.connect(self.on_edit)
        self.delete_button.clicked.connect(self.on_delete)
        self.launch_button.clicked.connect(self.on_launch)
        self.list_widget.model().rowsMoved.connect(self.on_rows_moved)

        self.ad_view = QWebEngineView()
        self.ad_view.setFixedHeight(70)
        self.ad_view.setPage(ExternalLinkPage(self.ad_view))
        layout.addWidget(self.ad_view)

        try:
            page_profile = self.ad_view.page().profile()
            custom_ua = get_system_or_random_ua()
            page_profile.setHttpUserAgent(custom_ua)
        except Exception:
            pass

        self.reload_ad()

    def commands_clicked(self):
        self.logic.open_commands()

    def about_clicked(self):
        self.logic.open_about_jivaro()

    def discord_clicked(self):
        self.logic.open_discord()

    def proxies_clicked(self):
        self.logic.open_proxies()  # Make sure this is defined in your logic

    def on_install(self):
        dialog = InstallProgressDialog(self)
        worker = InstallWorker()

        def handle_progress(val):
            dialog.update_progress(val)

        def handle_finished():
            dialog.close()

        worker.progress_signal.connect(handle_progress)
        worker.finished_signal.connect(handle_finished)
        th = threading.Thread(target=worker.run_install, daemon=True)
        th.start()
        dialog.exec()

    def reload_ad(self):
        ad_html = """
        <html>
          <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4223077320283786"
                    crossorigin="anonymous"></script>
          </head>
          <body style="background-color:#323232; margin:0; padding:0; text-align:center;">
            <ins class="adsbygoogle"
                 style="display:inline-block;width:320px;height:50px"
                 data-ad-client="ca-pub-4223077320283786"
                 data-ad-slot="7522220612"></ins>
            <script>
               (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
          </body>
        </html>
        """
        self.ad_view.setHtml(ad_html, QUrl("https://www.jivaro.net/downloads/programs/info/instanciar"))

    def on_rows_moved(self, parent, start, end, destination, row):
        self.logic.on_rows_moved(self.list_widget)

    def on_create(self):
        self.logic.create_instance(self, self.list_widget)

    def on_edit(self):
        self.logic.edit_instance(self, self.list_widget)

    def on_delete(self):
        self.logic.delete_instance(self.list_widget)

    def on_launch(self):
        self.logic.launch_instance_in_thread(self.list_widget)
