# gui/instance_manager.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QComboBox, QRadioButton, QButtonGroup, QStackedWidget,
    QWidget
)
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

class GuiInstanceManager(QDialog):
    def __init__(self, manager, instance_name, parent=None):
        super().__init__(parent)
        pal = self.palette()
        pal.setColor(pal.ColorRole.Window, QColor(50, 50, 50))
        pal.setColor(pal.ColorRole.WindowText, QColor(220, 220, 220))
        self.setPalette(pal)
        self.setModal(True)
        self.manager = manager
        self.instance_name = instance_name
        self.setWindowTitle("Instance Manager")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.name_label = QLabel("Instance Name")
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet("background-color: rgb(70,70,70); color: rgb(220,220,220);")

        self.use_proxy_checkbox = QCheckBox("Use Proxy")
        self.use_proxy_checkbox.setStyleSheet("color: rgb(220,220,220);")
        self.proxy_ip_label = QLabel("IP")
        self.proxy_ip_input = QLineEdit()
        self.proxy_ip_input.setStyleSheet("background-color: rgb(70,70,70); color: rgb(220,220,220);")
        self.proxy_port_label = QLabel("Port")
        self.proxy_port_input = QLineEdit()
        self.proxy_port_input.setStyleSheet("background-color: rgb(70,70,70); color: rgb(220,220,220);")
        self.proxy_protocol_label = QLabel("Protocol")
        self.proxy_protocol_combo = QComboBox()
        self.proxy_protocol_combo.setStyleSheet("background-color: rgb(70,70,70); color: rgb(220,220,220);")
        self.proxy_protocol_combo.addItems(["HTTP", "HTTPS", "SOCKS4", "SOCKS5"])
        self.proxy_auth_checkbox = QCheckBox("Require Authentication")
        self.proxy_auth_checkbox.setStyleSheet("color: rgb(220,220,220);")
        self.proxy_user_label = QLabel("Username")
        self.proxy_user_input = QLineEdit()
        self.proxy_user_input.setStyleSheet("background-color: rgb(70,70,70); color: rgb(220,220,220);")
        self.proxy_pass_label = QLabel("Password")
        self.proxy_pass_input = QLineEdit()
        self.proxy_pass_input.setStyleSheet("background-color: rgb(70,70,70); color: rgb(220,220,220);")

        self.hwid_checkbox = QCheckBox("Use Random HWID")
        self.hwid_checkbox.setStyleSheet("color: rgb(220,220,220);")

        self.antidetect_checkbox = QCheckBox("Antidetection")
        self.antidetect_checkbox.setStyleSheet("color: rgb(220,220,220);")

        # Time Zone
        self.timezone_label = QLabel("Time Zone")
        self.tz_radio_default = QRadioButton("Default")
        self.tz_radio_custom = QRadioButton("Custom")
        self.tz_radio_default.setStyleSheet("color: rgb(220,220,220);")
        self.tz_radio_custom.setStyleSheet("color: rgb(220,220,220);")
        self.tz_radio_default.setChecked(True)
        self.tz_group = QButtonGroup(self)
        self.tz_group.addButton(self.tz_radio_default)
        self.tz_group.addButton(self.tz_radio_custom)

        self.timezone_stack = QStackedWidget()
        # 1) Page 0 for default (a combo)
        self.tz_combo_page = QWidget()
        tz_combo_layout = QVBoxLayout(self.tz_combo_page)
        self.timezone_combo = QComboBox()
        self.timezone_combo.setStyleSheet("background-color: rgb(70,70,70); color: rgb(220,220,220);")
        timezones = [
            "Africa/Cairo", "Africa/Nairobi", "America/Chicago", "America/Denver",
            "America/Los_Angeles", "America/New_York", "America/Sao_Paulo", "Asia/Dubai",
            "Asia/Hong_Kong", "Asia/Kolkata", "Asia/Shanghai", "Asia/Singapore",
            "Asia/Tokyo", "Australia/Adelaide", "Australia/Brisbane", "Australia/Sydney",
            "Europe/Berlin", "Europe/London", "Europe/Moscow", "Europe/Paris",
            "Europe/Rome", "Pacific/Auckland", "Pacific/Honolulu", "UTC"
        ]
        self.timezone_combo.addItems(timezones)
        tz_combo_layout.addWidget(self.timezone_combo)

        # 2) Page 1 for custom (a line edit)
        self.tz_custom_page = QWidget()
        tz_custom_layout = QVBoxLayout(self.tz_custom_page)
        self.timezone_custom_input = QLineEdit()
        self.timezone_custom_input.setStyleSheet("background-color: rgb(70,70,70); color: rgb(220,220,220);")
        tz_custom_layout.addWidget(self.timezone_custom_input)

        self.timezone_stack.addWidget(self.tz_combo_page)   # index 0
        self.timezone_stack.addWidget(self.tz_custom_page)  # index 1

        # Language
        self.language_label = QLabel("Language")
        self.lang_radio_default = QRadioButton("Default")
        self.lang_radio_custom = QRadioButton("Custom")
        self.lang_radio_default.setStyleSheet("color: rgb(220,220,220);")
        self.lang_radio_custom.setStyleSheet("color: rgb(220,220,220);")
        self.lang_radio_default.setChecked(True)
        self.lang_group = QButtonGroup(self)
        self.lang_group.addButton(self.lang_radio_default)
        self.lang_group.addButton(self.lang_radio_custom)

        self.language_stack = QStackedWidget()
        # Page 0 for default
        self.lang_combo_page = QWidget()
        lang_combo_layout = QVBoxLayout(self.lang_combo_page)
        self.language_combo = QComboBox()
        self.language_combo.setStyleSheet("background-color: rgb(70,70,70); color: rgb(220,220,220);")
        languages = [
            "Arabic (ar)", "Bengali (bn)", "Chinese (zh)", "Dutch (nl)",
            "English (en)", "French (fr)", "German (de)", "Hindi (hi)",
            "Italian (it)", "Japanese (ja)", "Korean (ko)", "Malay (ms)",
            "Portuguese (pt)", "Punjabi (pa)", "Russian (ru)", "Spanish (es)",
            "Swahili (sw)", "Thai (th)", "Turkish (tr)", "Vietnamese (vi)"
        ]
        self.language_combo.addItems(languages)
        lang_combo_layout.addWidget(self.language_combo)

        # Page 1 for custom
        self.lang_custom_page = QWidget()
        lang_custom_layout = QVBoxLayout(self.lang_custom_page)
        self.language_custom_input = QLineEdit()
        self.language_custom_input.setStyleSheet("background-color: rgb(70,70,70); color: rgb(220,220,220);")
        lang_custom_layout.addWidget(self.language_custom_input)

        self.language_stack.addWidget(self.lang_combo_page)   # index 0
        self.language_stack.addWidget(self.lang_custom_page)  # index 1

        self.webrtc_checkbox = QCheckBox("Disable WebRTC")
        self.webrtc_checkbox.setStyleSheet("color: rgb(220,220,220);")

        self.geo_checkbox = QCheckBox("Enable Geolocation")
        self.geo_checkbox.setStyleSheet("color: rgb(220,220,220);")

        # User agent
        self.ua_label = QLabel("User Agent")
        self.ua_radio_default = QRadioButton("Default")
        self.ua_radio_custom = QRadioButton("Custom")
        self.ua_radio_default.setStyleSheet("color: rgb(220,220,220);")
        self.ua_radio_custom.setStyleSheet("color: rgb(220,220,220);")
        self.ua_radio_default.setChecked(True)
        self.ua_group = QButtonGroup(self)
        self.ua_group.addButton(self.ua_radio_default)
        self.ua_group.addButton(self.ua_radio_custom)

        self.ua_stack = QStackedWidget()
        # Page 0 for default
        self.ua_combo_page = QWidget()
        ua_combo_layout = QVBoxLayout(self.ua_combo_page)
        self.ua_combo = QComboBox()
        self.ua_combo.setStyleSheet("background-color: rgb(70,70,70); color: rgb(220,220,220);")
        common_user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/113.0.5672.63",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_3) Firefox/113.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1) Safari/604.1",
            "Mozilla/5.0 (Linux; Android 12) Chrome/112.0.5615.137",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edg/112.0.1722.64",
            "Mozilla/5.0 (X11; Linux x86_64) Chrome/113.0.5672.63",
            "Mozilla/5.0 (Windows NT 6.1; Win64; x64) Firefox/108.0",
            "Mozilla/5.0 (Linux; Android 11) Chrome/109.0.5414.119",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
            "Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1"
        ]
        self.ua_combo.addItems(common_user_agents)
        ua_combo_layout.addWidget(self.ua_combo)

        # Page 1 for custom
        self.ua_custom_page = QWidget()
        ua_custom_layout = QVBoxLayout(self.ua_custom_page)
        self.ua_input = QLineEdit()
        self.ua_input.setStyleSheet("background-color: rgb(70,70,70); color: rgb(220,220,220);")
        ua_custom_layout.addWidget(self.ua_input)

        self.ua_stack.addWidget(self.ua_combo_page)   # index 0
        self.ua_stack.addWidget(self.ua_custom_page)  # index 1

        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")

        # Layout construction
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.name_input)

        self.layout.addWidget(self.use_proxy_checkbox)
        self.layout.addWidget(self.proxy_ip_label)
        self.layout.addWidget(self.proxy_ip_input)
        self.layout.addWidget(self.proxy_port_label)
        self.layout.addWidget(self.proxy_port_input)
        self.layout.addWidget(self.proxy_protocol_label)
        self.layout.addWidget(self.proxy_protocol_combo)
        self.layout.addWidget(self.proxy_auth_checkbox)
        self.layout.addWidget(self.proxy_user_label)
        self.layout.addWidget(self.proxy_user_input)
        self.layout.addWidget(self.proxy_pass_label)
        self.layout.addWidget(self.proxy_pass_input)

        self.layout.addWidget(self.hwid_checkbox)
        self.layout.addWidget(self.antidetect_checkbox)

        self.layout.addWidget(self.timezone_label)
        tz_radio_layout = QHBoxLayout()
        tz_radio_layout.addWidget(self.tz_radio_default)
        tz_radio_layout.addWidget(self.tz_radio_custom)
        self.layout.addLayout(tz_radio_layout)
        self.layout.addWidget(self.timezone_stack)

        self.layout.addWidget(self.language_label)
        lang_radio_layout = QHBoxLayout()
        lang_radio_layout.addWidget(self.lang_radio_default)
        lang_radio_layout.addWidget(self.lang_radio_custom)
        self.layout.addLayout(lang_radio_layout)
        self.layout.addWidget(self.language_stack)

        self.layout.addWidget(self.webrtc_checkbox)
        self.layout.addWidget(self.geo_checkbox)

        self.layout.addWidget(self.ua_label)
        ua_radio_layout = QHBoxLayout()
        ua_radio_layout.addWidget(self.ua_radio_default)
        ua_radio_layout.addWidget(self.ua_radio_custom)
        self.layout.addLayout(ua_radio_layout)
        self.layout.addWidget(self.ua_stack)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(button_layout)

        self.use_proxy_checkbox.stateChanged.connect(self.on_proxy_checkbox_changed)
        self.proxy_auth_checkbox.stateChanged.connect(self.on_proxy_auth_checkbox_changed)

        # Connect radio toggles
        self.tz_radio_default.toggled.connect(self.on_tz_radio_toggled)
        self.lang_radio_default.toggled.connect(self.on_lang_radio_toggled)
        self.ua_radio_default.toggled.connect(self.on_ua_radio_toggled)

        self.save_button.clicked.connect(self.save)
        self.cancel_button.clicked.connect(self.reject)

        self.load_existing()
        self.apply_current_states()
        self.on_tz_radio_toggled()
        self.on_lang_radio_toggled()
        self.on_ua_radio_toggled()

    def apply_current_states(self):
        if self.use_proxy_checkbox.isChecked():
            self.proxy_ip_input.setEnabled(True)
            self.proxy_port_input.setEnabled(True)
            self.proxy_protocol_combo.setEnabled(True)
            self.proxy_auth_checkbox.setEnabled(True)
            if self.proxy_auth_checkbox.isChecked():
                self.proxy_user_input.setEnabled(True)
                self.proxy_pass_input.setEnabled(True)
            else:
                self.proxy_user_input.setEnabled(False)
                self.proxy_pass_input.setEnabled(False)
        else:
            self.proxy_ip_input.setEnabled(False)
            self.proxy_port_input.setEnabled(False)
            self.proxy_protocol_combo.setEnabled(False)
            self.proxy_auth_checkbox.setEnabled(False)
            self.proxy_user_input.setEnabled(False)
            self.proxy_pass_input.setEnabled(False)

    def on_proxy_checkbox_changed(self, state):
        self.apply_current_states()

    def on_proxy_auth_checkbox_changed(self, state):
        self.apply_current_states()

    # Switch between combo and custom text for timezone
    def on_tz_radio_toggled(self):
        if self.tz_radio_default.isChecked():
            self.timezone_stack.setCurrentIndex(0)  # show combo
        else:
            self.timezone_stack.setCurrentIndex(1)  # show text

    # Switch between combo and custom text for language
    def on_lang_radio_toggled(self):
        if self.lang_radio_default.isChecked():
            self.language_stack.setCurrentIndex(0)
        else:
            self.language_stack.setCurrentIndex(1)

    # Switch between combo and custom text for user agent
    def on_ua_radio_toggled(self):
        if self.ua_radio_default.isChecked():
            self.ua_stack.setCurrentIndex(0)
        else:
            self.ua_stack.setCurrentIndex(1)

    def load_existing(self):
        if self.instance_name:
            instance = self.manager.get_instance(self.instance_name)
            if instance:
                self.name_input.setText(instance["name"])
                if instance.get("proxy"):
                    self.use_proxy_checkbox.setChecked(True)
                    self.proxy_ip_input.setText(instance["proxy"]["ip"])
                    self.proxy_port_input.setText(instance["proxy"]["port"])
                    if instance["proxy"]["protocol"] in ["HTTP", "HTTPS", "SOCKS4", "SOCKS5"]:
                        idx = self.proxy_protocol_combo.findText(instance["proxy"]["protocol"])
                        if idx >= 0:
                            self.proxy_protocol_combo.setCurrentIndex(idx)
                    if instance["proxy"]["auth"]:
                        self.proxy_auth_checkbox.setChecked(True)
                        self.proxy_user_input.setText(instance["proxy"]["user"])
                        self.proxy_pass_input.setText(instance["proxy"]["password"])

                if instance.get("hwid", {}).get("enabled"):
                    self.hwid_checkbox.setChecked(True)

                if instance.get("antidetect", {}).get("enabled"):
                    self.antidetect_checkbox.setChecked(True)

                # Identity
                if "identity" in instance:
                    ident = instance["identity"]
                    # Time Zone
                    if "timezone" in ident:
                        # check if it's in the combo
                        tz = ident["timezone"]
                        combo_items = [self.timezone_combo.itemText(i) for i in range(self.timezone_combo.count())]
                        if tz in combo_items:
                            self.tz_radio_default.setChecked(True)
                            idx_tz = self.timezone_combo.findText(tz)
                            if idx_tz >= 0:
                                self.timezone_combo.setCurrentIndex(idx_tz)
                        else:
                            self.tz_radio_custom.setChecked(True)
                            self.timezone_custom_input.setText(tz)

                    # Language
                    if "language" in ident:
                        lang = ident["language"]
                        lang_items = [self.language_combo.itemText(i) for i in range(self.language_combo.count())]
                        if lang in lang_items:
                            self.lang_radio_default.setChecked(True)
                            idx_lang = self.language_combo.findText(lang)
                            if idx_lang >= 0:
                                self.language_combo.setCurrentIndex(idx_lang)
                        else:
                            self.lang_radio_custom.setChecked(True)
                            self.language_custom_input.setText(lang)

                    # WebRTC
                    if ident.get("webrtc_disabled"):
                        self.webrtc_checkbox.setChecked(True)
                    # Geolocation
                    if ident.get("geolocation_enabled"):
                        self.geo_checkbox.setChecked(True)

                    # User agent
                    if "custom_user_agent" in ident:
                        ua = ident["custom_user_agent"]
                        ua_items = [self.ua_combo.itemText(i) for i in range(self.ua_combo.count())]
                        if ua in ua_items:
                            self.ua_radio_default.setChecked(True)
                            idx_ua = self.ua_combo.findText(ua)
                            if idx_ua >= 0:
                                self.ua_combo.setCurrentIndex(idx_ua)
                        else:
                            self.ua_radio_custom.setChecked(True)
                            self.ua_input.setText(ua)

                # Ensure the correct stacked pages are visible
                self.on_tz_radio_toggled()
                self.on_lang_radio_toggled()
                self.on_ua_radio_toggled()

    def save(self):
        name = self.name_input.text()
        px_enabled = self.use_proxy_checkbox.isChecked()
        ip = self.proxy_ip_input.text()
        port = self.proxy_port_input.text()
        protocol = self.proxy_protocol_combo.currentText()
        auth_enabled = self.proxy_auth_checkbox.isChecked()
        user = self.proxy_user_input.text()
        password = self.proxy_pass_input.text()
        hwid_enabled = self.hwid_checkbox.isChecked()
        antidetect_enabled = self.antidetect_checkbox.isChecked()

        # Time zone
        if self.tz_radio_default.isChecked():
            tz_val = self.timezone_combo.currentText()
        else:
            tz_val = self.timezone_custom_input.text()

        # Language
        if self.lang_radio_default.isChecked():
            lang_val = self.language_combo.currentText()
        else:
            lang_val = self.language_custom_input.text()

        webrtc_off = self.webrtc_checkbox.isChecked()
        geo_on = self.geo_checkbox.isChecked()

        # UA
        if self.ua_radio_default.isChecked():
            ua_val = self.ua_combo.currentText()
        else:
            ua_val = self.ua_input.text()

        self.manager.save_instance_extended(
            old_name=self.instance_name,
            new_name=name,
            proxy_enabled=px_enabled,
            ip=ip,
            port=port,
            protocol=protocol,
            auth_enabled=auth_enabled,
            user=user,
            password=password,
            hwid_enabled=hwid_enabled,
            antidetect_enabled=antidetect_enabled,
            timezone=tz_val,
            language=lang_val,
            webrtc_disabled=webrtc_off,
            geolocation_enabled=geo_on,
            custom_ua=ua_val
        )
        self.accept()
