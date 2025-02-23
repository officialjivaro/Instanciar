# appdata/gui/main_window.py
import platform
import threading
import time
import random
import os
import sys
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QAbstractItemView,
    QComboBox,
    QCheckBox,
    QMenuBar,
    QLabel
)
from PySide6.QtGui import QPalette, QColor, QDesktopServices, QIcon, QAction
from PySide6.QtCore import Qt, QUrl, QMetaObject
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage
from appdata.logic.instance_manager import LogicInstanceManager
from appdata.logic.main_window import MainWindowLogic

def rp(x):
    if hasattr(sys, '_MEIPASS'):
        b = sys._MEIPASS
    else:
        b = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(b, x)

class ExternalLinkPage(QWebEnginePage):
    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        if nav_type == QWebEnginePage.NavigationTypeLinkClicked:
            QDesktopServices.openUrl(url)
            return False
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        i = rp("appdata/media/icon.ico")
        self.setWindowIcon(QIcon(i))
        self.setWindowTitle("Instanciar v0.03")
        self.resize(400, 400)
        p = self.palette()
        p.setColor(QPalette.Window, QColor(50, 50, 50))
        p.setColor(QPalette.WindowText, QColor(220, 220, 220))
        self.setPalette(p)
        bar = QMenuBar(self)
        bar.setStyleSheet(
            "QMenuBar { background-color: rgb(50, 50, 50); color: rgb(220,220,220); }"
            "QMenuBar::item:selected { background-color: rgb(70,70,70); }"
            "QMenu { background-color: rgb(50,50,50); color: rgb(220,220,220); }"
            "QMenu::item:selected { background-color: rgb(70,70,70); }"
        )
        self.setMenuBar(bar)
        fm = bar.addMenu("File")
        ia = QAction("Install", self)
        ia.triggered.connect(self.on_install)
        exa = QAction("Exit", self)
        exa.triggered.connect(self.close)
        fm.addAction(ia)
        fm.addAction(exa)
        c = QWidget()
        self.setCentralWidget(c)
        lay = QVBoxLayout()
        c.setLayout(lay)
        top_label = QLabel("Instance List")
        top_label.setAlignment(Qt.AlignHCenter)
        lay.addWidget(top_label)
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        lay.addWidget(self.list_widget)
        row = QHBoxLayout()
        self.browser_combo = QComboBox()
        if platform.system().lower() == "darwin":
            self.browser_combo.addItems(["Chrome", "Firefox", "Safari"])
        else:
            self.browser_combo.addItems(["Chrome", "Firefox"])
        row.addWidget(self.browser_combo)
        self.block_checkbox = QCheckBox("Copy/Paste/PrtSc Antidetection")
        row.addWidget(self.block_checkbox)
        lay.addLayout(row)
        btns = QHBoxLayout()
        self.create_button = QPushButton("Create")
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")
        self.launch_button = QPushButton("Launch")
        btns.addWidget(self.create_button)
        btns.addWidget(self.edit_button)
        btns.addWidget(self.delete_button)
        btns.addWidget(self.launch_button)
        lay.addLayout(btns)
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
        lay.addWidget(self.ad_view)
        self.reload_ad()
        self.start_ad_reload_thread()

    def on_install(self):
        self.logic.install_app()

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
                 data-ad-slot="4075767995"></ins>
            <script>
               (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
          </body>
        </html>
        """
        self.ad_view.setHtml(ad_html, QUrl("https://www.jivaro.net"))

    def start_ad_reload_thread(self):
        def worker():
            while True:
                interval = random.randint(10, 110) * 60
                time.sleep(interval)
                QMetaObject.invokeMethod(self, "reload_ad", Qt.QueuedConnection)
        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def on_rows_moved(self, parent, start, end, destination, row):
        self.logic.on_rows_moved(self.list_widget)

    def on_create(self):
        self.logic.create_instance(self, self.list_widget)

    def on_edit(self):
        self.logic.edit_instance(self, self.list_widget)

    def on_delete(self):
        self.logic.delete_instance(self.list_widget)

    def on_launch(self):
        self.logic.launch_instance_in_thread(self.list_widget, self.browser_combo, self.block_checkbox)
