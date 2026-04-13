# appdata/gui/instance_manager.py
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QComboBox,
    QRadioButton,
    QButtonGroup,
    QStackedWidget,
    QWidget,
    QGroupBox,
    QFormLayout,
    QFrame,
    QMessageBox,
)
from PySide6.QtGui import QPalette, QColor, QFont

from appdata.logic.group_manager import GroupManagerLogic
from appdata.config.constants import TIME_ZONES, LANGUAGES
from appdata.config.style_constants import BACKGROUND_MAIN, TEXT_COLOR, GROUP_HOVER, ACCENT_COLOR
from appdata.utils.browser_identity import (
    get_latest_stable_identity,
    identity_from_user_agent,
    list_recent_real_identities,
    normalize_identity_selection,
)


class GuiInstanceManager(QDialog):
    instanceSaved = Signal(str)

    def __init__(self, manager, instance_name, parent=None):
        super().__init__(parent)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(BACKGROUND_MAIN))
        palette.setColor(QPalette.WindowText, QColor(TEXT_COLOR))
        palette.setColor(QPalette.Base, QColor(BACKGROUND_MAIN))
        palette.setColor(QPalette.Button, QColor(BACKGROUND_MAIN))
        palette.setColor(QPalette.ButtonText, QColor(TEXT_COLOR))
        self.setPalette(palette)
        self.setFont(QFont("Segoe UI", 11))
        self.setStyleSheet(
            f"""
            QDialog        {{ background:{BACKGROUND_MAIN}; }}
            QLabel         {{ color:{TEXT_COLOR}; }}
            QLineEdit      {{ background:{GROUP_HOVER}; color:{TEXT_COLOR}; border-radius:3px; padding:4px; }}
            QLineEdit:focus{{ border:1px solid {ACCENT_COLOR}; }}
            QComboBox      {{ background:{GROUP_HOVER}; color:{TEXT_COLOR}; border-radius:3px; padding:2px 4px; }}
            QPushButton    {{ background:{BACKGROUND_MAIN}; color:{TEXT_COLOR}; border:1px solid {GROUP_HOVER}; border-radius:4px; padding:6px 12px; }}
            QPushButton:hover{{ background:{GROUP_HOVER}; border:1px solid {ACCENT_COLOR}; }}
            QCheckBox      {{ color:{TEXT_COLOR}; }}
            QGroupBox:title{{ color:{TEXT_COLOR}; subcontrol-origin: margin; left:10px; padding:0 3px 0 3px; }}
            """
        )

        self.resize(700, 500)
        self.setModal(True)
        self.manager = manager
        self.instance_name = instance_name
        self._recent_identities = []
        self.setWindowTitle("Instance Manager")

        main = QVBoxLayout(self)
        main.setContentsMargins(15, 15, 15, 15)
        main.setSpacing(12)

        head = QLabel("Manage Instance")
        head.setFont(QFont("Segoe UI", 13, QFont.Bold))
        head.setAlignment(Qt.AlignHCenter)
        main.addWidget(head)

        main.addWidget(QLabel("Configure proxy, identity, landing page and browser identity.", wordWrap=True))
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main.addWidget(line)

        basic = QGroupBox("Basic Info")
        basic_form = QFormLayout(basic)
        self.name_in = QLineEdit()
        self.group_cb = QComboBox()
        self.group_cb.addItems(GroupManagerLogic().get_all_groups())
        self.landing_in = QLineEdit("https://www.duckduckgo.com")
        basic_form.addRow(QLabel("Instance Name:"), self.name_in)
        basic_form.addRow(QLabel("Group:"), self.group_cb)
        basic_form.addRow(QLabel("Landing Page:"), self.landing_in)
        main.addWidget(basic)

        proxy_box = QGroupBox("Proxy Settings")
        proxy_layout = QVBoxLayout(proxy_box)
        self.use_proxy = QCheckBox("Use Proxy")
        proxy_layout.addWidget(self.use_proxy)

        proxy_form = QFormLayout()
        self.ip_in = QLineEdit()
        self.port_in = QLineEdit()
        self.proto_cb = QComboBox()
        self.proto_cb.addItems(["HTTP", "HTTPS", "SOCKS4", "SOCKS5"])
        self.auth_ck = QCheckBox("Require Authentication")
        self.user_in = QLineEdit()
        self.pass_in = QLineEdit()

        proxy_form.addRow(QLabel("IP:"), self.ip_in)
        proxy_form.addRow(QLabel("Port:"), self.port_in)
        proxy_form.addRow(QLabel("Protocol:"), self.proto_cb)
        proxy_form.addRow(self.auth_ck, QLabel(""))
        proxy_form.addRow(QLabel("Username:"), self.user_in)
        proxy_form.addRow(QLabel("Password:"), self.pass_in)
        proxy_layout.addLayout(proxy_form)
        main.addWidget(proxy_box)

        identity_box = QGroupBox("Identity & Fingerprint")
        identity_layout = QVBoxLayout(identity_box)

        advanced_row = QHBoxLayout()
        self.hwid_ck = QCheckBox("Use Random HWID")
        self.anti_ck = QCheckBox("Antidetection")
        advanced_row.addWidget(self.hwid_ck)
        advanced_row.addWidget(self.anti_ck)
        identity_layout.addLayout(advanced_row)

        self.tz_stack = self._make_stack("Time Zone:", TIME_ZONES, identity_layout)
        self.lang_stack = self._make_stack("Language:", LANGUAGES, identity_layout)

        checks = QHBoxLayout()
        self.webrtc_ck = QCheckBox("Disable WebRTC")
        self.geo_ck = QCheckBox("Enable Geolocation")
        checks.addWidget(self.webrtc_ck)
        checks.addWidget(self.geo_ck)
        identity_layout.addLayout(checks)

        self.ua_ctrl = self._make_ua_control(identity_layout)
        main.addWidget(identity_box)

        buttons = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)
        main.addLayout(buttons)

        self.use_proxy.stateChanged.connect(self._sync_proxy)
        self.auth_ck.stateChanged.connect(self._sync_proxy)
        self.save_btn.clicked.connect(self._save)
        self.cancel_btn.clicked.connect(self.reject)

        self._sync_proxy()
        self._load_existing()

    def _make_stack(self, label, items, parent_layout):
        form = QFormLayout()
        rb_default = QRadioButton("Default")
        rb_custom = QRadioButton("Custom")
        rb_default.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(rb_default)
        group.addButton(rb_custom)

        radio_layout = QHBoxLayout()
        radio_layout.addWidget(rb_default)
        radio_layout.addWidget(rb_custom)

        stack = QStackedWidget()
        page_combo = QWidget()
        combo_layout = QVBoxLayout(page_combo)
        combo_layout.setContentsMargins(0, 0, 0, 0)
        combo = QComboBox()
        combo.addItems(items)
        combo_layout.addWidget(combo)
        stack.addWidget(page_combo)

        page_custom = QWidget()
        custom_layout = QVBoxLayout(page_custom)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        line_edit = QLineEdit()
        custom_layout.addWidget(line_edit)
        stack.addWidget(page_custom)

        rb_default.toggled.connect(lambda: stack.setCurrentIndex(0 if rb_default.isChecked() else 1))

        form.addRow(QLabel(label), radio_layout)
        form.addRow(QLabel(""), stack)
        parent_layout.addLayout(form)
        return {"rb_def": rb_default, "cb": combo, "le": line_edit, "stack": stack}

    def _populate_recent_identity_choices(self):
        self._recent_identities = list_recent_real_identities(limit=6)
        self.ua_ctrl["cb"].clear()
        for identity in self._recent_identities:
            self.ua_ctrl["cb"].addItem(identity["label"], identity)

        latest = get_latest_stable_identity()
        self.ua_ctrl["latest_label"].setText(
            f'{latest["label"]}\n{latest["user_agent"]}'
        )

    def _make_ua_control(self, parent_layout):
        form = QFormLayout()

        rb_random = QRadioButton("Random Real")
        rb_latest = QRadioButton("Latest Stable (Real)")
        rb_list = QRadioButton("Select Recent Real")
        rb_custom = QRadioButton("Custom")
        rb_random.setChecked(True)

        group = QButtonGroup(self)
        for button in (rb_random, rb_latest, rb_list, rb_custom):
            group.addButton(button)

        top = QHBoxLayout()
        top.addWidget(rb_random)
        top.addWidget(rb_latest)
        top.addWidget(rb_list)
        top.addWidget(rb_custom)

        stack = QStackedWidget()

        page_random = QWidget()
        random_layout = QVBoxLayout(page_random)
        random_layout.setContentsMargins(0, 0, 0, 0)
        random_label = QLabel("Uses a recent real desktop Chrome identity for your current OS family.")
        random_label.setWordWrap(True)
        random_layout.addWidget(random_label)
        stack.addWidget(page_random)

        page_latest = QWidget()
        latest_layout = QVBoxLayout(page_latest)
        latest_layout.setContentsMargins(0, 0, 0, 0)
        latest_label = QLabel()
        latest_label.setWordWrap(True)
        latest_layout.addWidget(latest_label)
        stack.addWidget(page_latest)

        page_list = QWidget()
        list_layout = QVBoxLayout(page_list)
        list_layout.setContentsMargins(0, 0, 0, 0)
        combo = QComboBox()
        list_layout.addWidget(combo)
        stack.addWidget(page_list)

        page_custom = QWidget()
        custom_layout = QVBoxLayout(page_custom)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        line_edit = QLineEdit()
        custom_layout.addWidget(line_edit)
        stack.addWidget(page_custom)

        def sync():
            if rb_random.isChecked():
                stack.setCurrentIndex(0)
            elif rb_latest.isChecked():
                stack.setCurrentIndex(1)
            elif rb_list.isChecked():
                stack.setCurrentIndex(2)
            else:
                stack.setCurrentIndex(3)

        rb_random.toggled.connect(sync)
        rb_latest.toggled.connect(sync)
        rb_list.toggled.connect(sync)
        rb_custom.toggled.connect(sync)

        form.addRow(QLabel("Browser Identity:"), top)
        form.addRow(QLabel(""), stack)
        parent_layout.addLayout(form)

        ctrl = {
            "rb_rand": rb_random,
            "rb_latest": rb_latest,
            "rb_list": rb_list,
            "rb_cust": rb_custom,
            "cb": combo,
            "le": line_edit,
            "stack": stack,
            "latest_label": latest_label,
        }

        self.ua_ctrl = ctrl
        self._populate_recent_identity_choices()
        sync()
        return ctrl

    def _sync_proxy(self):
        enabled = self.use_proxy.isChecked()
        for widget in (self.ip_in, self.port_in, self.proto_cb, self.auth_ck):
            widget.setEnabled(enabled)

        auth_enabled = enabled and self.auth_ck.isChecked()
        for widget in (self.user_in, self.pass_in):
            widget.setEnabled(auth_enabled)

    def _select_group(self, name):
        index = self.group_cb.findText(name, Qt.MatchFixedString)
        if index == -1:
            self.group_cb.addItem(name)
            index = self.group_cb.count() - 1
        self.group_cb.setCurrentIndex(index)

    def _set_stack(self, stack_info, value, pool):
        if not value:
            return
        if value in pool:
            stack_info["rb_def"].setChecked(True)
            stack_info["cb"].setCurrentText(value)
        else:
            stack_info["rb_def"].setChecked(False)
            stack_info["le"].setText(value)

    def _select_recent_identity(self, preset_key, custom_ua):
        if preset_key:
            for index in range(self.ua_ctrl["cb"].count()):
                ident = self.ua_ctrl["cb"].itemData(index)
                if ident and ident.get("preset_key") == preset_key:
                    self.ua_ctrl["cb"].setCurrentIndex(index)
                    return True

        if custom_ua:
            legacy = identity_from_user_agent(custom_ua)
            legacy["label"] = f'Legacy preset • {legacy["platform_label"]} • Chrome {legacy["major_version"]}'
            self.ua_ctrl["cb"].addItem(legacy["label"], legacy)
            self.ua_ctrl["cb"].setCurrentIndex(self.ua_ctrl["cb"].count() - 1)
            return True

        return False

    def _load_existing(self):
        if not self.instance_name:
            self._select_group("Unassigned")
            return

        inst = self.manager.get_instance(self.instance_name) or {}
        self.name_in.setText(inst.get("name", ""))
        self._select_group(inst.get("group", "Unassigned"))
        self.landing_in.setText(inst.get("landing_page", "https://www.duckduckgo.com"))

        proxy = inst.get("proxy")
        if proxy:
            self.use_proxy.setChecked(True)
            self.ip_in.setText(proxy.get("ip", ""))
            self.port_in.setText(proxy.get("port", ""))
            self.proto_cb.setCurrentText(proxy.get("protocol", ""))
            self.auth_ck.setChecked(proxy.get("auth", False))
            if proxy.get("auth"):
                self.user_in.setText(proxy.get("user", ""))
                self.pass_in.setText(proxy.get("password", ""))

        if inst.get("hwid", {}).get("enabled"):
            self.hwid_ck.setChecked(True)
        if inst.get("antidetect", {}).get("enabled"):
            self.anti_ck.setChecked(True)

        identity = inst.get("identity", {})
        self._set_stack(self.tz_stack, identity.get("timezone"), TIME_ZONES)
        self._set_stack(self.lang_stack, identity.get("language"), LANGUAGES)

        normalized = normalize_identity_selection(identity)
        mode = normalized["mode"]
        preset_key = normalized["preset_key"]
        custom_ua = normalized["custom_user_agent"]

        if mode == "latest_stable_real":
            self.ua_ctrl["rb_latest"].setChecked(True)
        elif mode == "preset_real" and self._select_recent_identity(preset_key, custom_ua):
            self.ua_ctrl["rb_list"].setChecked(True)
        elif mode == "custom":
            self.ua_ctrl["rb_cust"].setChecked(True)
            self.ua_ctrl["le"].setText(custom_ua or "")
        else:
            self.ua_ctrl["rb_rand"].setChecked(True)

        if identity.get("webrtc_disabled"):
            self.webrtc_ck.setChecked(True)
        if identity.get("geolocation_enabled"):
            self.geo_ck.setChecked(True)

    def _selected_browser_identity(self):
        if self.ua_ctrl["rb_rand"].isChecked():
            return {"mode": "random_real", "preset": "", "custom_ua": ""}

        if self.ua_ctrl["rb_latest"].isChecked():
            latest = get_latest_stable_identity()
            return {"mode": "latest_stable_real", "preset": "", "custom_ua": latest["user_agent"]}

        if self.ua_ctrl["rb_list"].isChecked():
            identity = self.ua_ctrl["cb"].currentData() or get_latest_stable_identity()
            return {
                "mode": "preset_real",
                "preset": identity.get("preset_key", ""),
                "custom_ua": identity.get("user_agent", ""),
            }

        custom_ua = self.ua_ctrl["le"].text().strip()
        if not custom_ua:
            custom_ua = get_latest_stable_identity()["user_agent"]
        return {"mode": "custom", "preset": "", "custom_ua": custom_ua}

    def _show_save_error(self, message):
        QMessageBox.warning(self, "Cannot Save Instance", message)

    def _validate_before_save(self, name, proxy):
        """Ask the logic layer to validate before attempting a real save."""
        result = self.manager.validate_instance_inputs(
            old_name=self.instance_name,
            new_name=name,
            proxy_enabled=bool(proxy),
            ip=proxy["ip"] if proxy else "",
            port=proxy["port"] if proxy else "",
            auth_enabled=proxy["auth"] if proxy else False,
            user=proxy["user"] if proxy else "",
            password=proxy["password"] if proxy else "",
        )
        if not result:
            self._show_save_error(result.message)
        return result

    def _save(self):
        name = self.name_in.text().strip()

        proxy = None
        if self.use_proxy.isChecked():
            proxy = {
                "ip": self.ip_in.text().strip(),
                "port": self.port_in.text().strip(),
                "protocol": self.proto_cb.currentText(),
                "auth": self.auth_ck.isChecked(),
                "user": self.user_in.text().strip(),
                "password": self.pass_in.text().strip(),
            }

        validation = self._validate_before_save(name, proxy)
        if not validation:
            return

        # Use the trimmed/validated name from the logic layer.
        name = validation.name or name

        def value_from(stack_info):
            return stack_info["cb"].currentText() if stack_info["rb_def"].isChecked() else stack_info["le"].text().strip()

        browser_identity = self._selected_browser_identity()

        result = self.manager.save_instance_extended(
            old_name=self.instance_name,
            new_name=name,
            proxy_enabled=bool(proxy),
            ip=proxy["ip"] if proxy else "",
            port=proxy["port"] if proxy else "",
            protocol=proxy["protocol"] if proxy else "",
            auth_enabled=proxy["auth"] if proxy else False,
            user=proxy["user"] if proxy else "",
            password=proxy["password"] if proxy else "",
            hwid_enabled=self.hwid_ck.isChecked(),
            antidetect_enabled=self.anti_ck.isChecked(),
            timezone=value_from(self.tz_stack),
            language=value_from(self.lang_stack),
            webrtc_disabled=self.webrtc_ck.isChecked(),
            geolocation_enabled=self.geo_ck.isChecked(),
            custom_ua=browser_identity["custom_ua"],
            landing_page=self.landing_in.text().strip(),
            browser_identity_mode=browser_identity["mode"],
            browser_identity_preset=browser_identity["preset"],
        )
        if not result:
            self._show_save_error(result.message or "The instance could not be saved.")
            return

        saved_name = result.name or name
        self.manager.save_instance_group(saved_name, self.group_cb.currentText() or "Unassigned")
        self.instanceSaved.emit(saved_name)
        self.accept()