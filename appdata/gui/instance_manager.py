# appdata/gui/instance_manager.py
import html

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from appdata.config.constants import LANGUAGES, TIME_ZONES
from appdata.config.style_constants import FONT_FAMILY, FONT_SIZE
from appdata.gui.themes.app_theme import apply_app_theme, set_widget_role
from appdata.logic.browser_profile_health import build_browser_profile_health
from appdata.logic.group_manager import GroupManagerLogic
from appdata.logic.region_profile_logic import (
    get_launch_mode_choices,
    get_region_choices,
    get_region_profile,
    normalize_launch_mode,
    normalize_region_profile_key,
    region_defaults_for_key,
)
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
        self.manager = manager
        self.instance_name = instance_name
        self._recent_identities = []

        self.setObjectName("DialogRoot")
        self.setWindowTitle("Instance Manager")
        self.resize(780, 620)
        self.setModal(True)
        self.setFont(QFont(FONT_FAMILY, FONT_SIZE))
        apply_app_theme(self)

        main = QVBoxLayout(self)
        main.setContentsMargins(16, 16, 16, 16)
        main.setSpacing(12)

        header = QLabel("Manage Instance")
        header.setAlignment(Qt.AlignHCenter)
        header.setFont(QFont(FONT_FAMILY, FONT_SIZE + 4, QFont.Bold))
        set_widget_role(header, "sectionTitle")
        main.addWidget(header)

        subtitle = QLabel(
            "Configure the instance profile, proxy, region, browser mode, and launch settings."
        )
        subtitle.setAlignment(Qt.AlignHCenter)
        subtitle.setWordWrap(True)
        set_widget_role(subtitle, "sectionHint")
        main.addWidget(subtitle)

        self.tabs = QTabWidget(self)
        self.tabs.addTab(self._build_basic_tab(), "Basic")
        self.tabs.addTab(self._build_proxy_tab(), "Proxy")
        self.tabs.addTab(self._build_region_tab(), "Region")
        self.tabs.addTab(self._build_browser_tab(), "Browser Profile")
        self.tabs.addTab(self._build_health_tab(), "Health Check")
        main.addWidget(self.tabs, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)

        self.save_btn = QPushButton("Save")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        set_widget_role(self.save_btn, "primary")

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        set_widget_role(self.cancel_btn, "secondary")

        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)
        main.addLayout(buttons)

        self._connect_signals()
        self._sync_proxy()
        self._load_existing()
        self._refresh_health()

    def _scroll_tab(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setWidget(widget)
        return scroll

    def _build_basic_tab(self) -> QScrollArea:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        basic = QGroupBox("Basic Info")
        basic_form = QFormLayout(basic)
        basic_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        basic_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.name_in = QLineEdit()
        self.name_in.setPlaceholderText("Example: Client Portal US")

        self.group_cb = QComboBox()
        self.group_cb.addItems(GroupManagerLogic().get_all_groups())

        self.landing_in = QLineEdit("https://www.duckduckgo.com")
        self.landing_in.setPlaceholderText("https://example.com")

        basic_form.addRow(QLabel("Instance Name:"), self.name_in)
        basic_form.addRow(QLabel("Group:"), self.group_cb)
        basic_form.addRow(QLabel("Landing Page:"), self.landing_in)
        layout.addWidget(basic)

        hint = QLabel(
            "Tip: use a clear instance name so it is easy to identify from the main window."
        )
        hint.setWordWrap(True)
        set_widget_role(hint, "sectionHint")
        layout.addWidget(hint)
        layout.addStretch(1)
        return self._scroll_tab(page)

    def _build_proxy_tab(self) -> QScrollArea:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        proxy_box = QGroupBox("Proxy Settings")
        proxy_layout = QVBoxLayout(proxy_box)
        proxy_layout.setSpacing(10)

        self.use_proxy = QCheckBox("Use Proxy")
        proxy_layout.addWidget(self.use_proxy)

        proxy_form = QFormLayout()
        proxy_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        proxy_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.ip_in = QLineEdit()
        self.ip_in.setPlaceholderText("Proxy host or IP")
        self.port_in = QLineEdit()
        self.port_in.setPlaceholderText("Port")
        self.proto_cb = QComboBox()
        self.proto_cb.addItems(["HTTP", "HTTPS", "SOCKS4", "SOCKS5"])
        self.auth_ck = QCheckBox("Require Authentication")
        self.user_in = QLineEdit()
        self.pass_in = QLineEdit()
        self.pass_in.setEchoMode(QLineEdit.EchoMode.Password)

        proxy_form.addRow(QLabel("IP / Host:"), self.ip_in)
        proxy_form.addRow(QLabel("Port:"), self.port_in)
        proxy_form.addRow(QLabel("Protocol:"), self.proto_cb)
        proxy_form.addRow(QLabel("Authentication:"), self.auth_ck)
        proxy_form.addRow(QLabel("Username:"), self.user_in)
        proxy_form.addRow(QLabel("Password:"), self.pass_in)
        proxy_layout.addLayout(proxy_form)
        layout.addWidget(proxy_box)

        hint = QLabel(
            "Region Profile does not test the proxy country. It only helps keep timezone, language, and browser settings consistent."
        )
        hint.setWordWrap(True)
        set_widget_role(hint, "sectionHint")
        layout.addWidget(hint)
        layout.addStretch(1)
        return self._scroll_tab(page)

    def _build_region_tab(self) -> QScrollArea:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        region_box = QGroupBox("Region Profile")
        region_form = QFormLayout(region_box)
        region_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        region_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.region_cb = QComboBox()
        for key, label in get_region_choices():
            self.region_cb.addItem(label, key)

        self.apply_region_btn = QPushButton("Apply Region Defaults")
        self.apply_region_btn.setCursor(Qt.PointingHandCursor)
        set_widget_role(self.apply_region_btn, "secondary")

        region_form.addRow(QLabel("Region:"), self.region_cb)
        region_form.addRow(QLabel(""), self.apply_region_btn)
        layout.addWidget(region_box)

        locale_box = QGroupBox("Timezone & Language")
        locale_layout = QVBoxLayout(locale_box)
        self.tz_stack = self._make_stack("Time Zone:", TIME_ZONES, locale_layout)
        self.lang_stack = self._make_stack("Language:", LANGUAGES, locale_layout)
        layout.addWidget(locale_box)

        self.region_hint = QLabel("")
        self.region_hint.setWordWrap(True)
        set_widget_role(self.region_hint, "sectionHint")
        layout.addWidget(self.region_hint)
        layout.addStretch(1)
        return self._scroll_tab(page)

    def _build_browser_tab(self) -> QScrollArea:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        launch_box = QGroupBox("Launch Mode")
        launch_form = QFormLayout(launch_box)
        launch_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        launch_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.launch_mode_cb = QComboBox()
        for key, label, description in get_launch_mode_choices():
            self.launch_mode_cb.addItem(label, key)
            self.launch_mode_cb.setItemData(self.launch_mode_cb.count() - 1, description, Qt.ToolTipRole)

        self.launch_mode_hint = QLabel("")
        self.launch_mode_hint.setWordWrap(True)
        set_widget_role(self.launch_mode_hint, "sectionHint")

        launch_form.addRow(QLabel("Browser Mode:"), self.launch_mode_cb)
        launch_form.addRow(QLabel(""), self.launch_mode_hint)
        layout.addWidget(launch_box)

        identity_box = QGroupBox("Identity & Permissions")
        identity_layout = QVBoxLayout(identity_box)
        identity_layout.setSpacing(10)

        advanced_row = QHBoxLayout()
        self.hwid_ck = QCheckBox("Use Random HWID")
        advanced_row.addWidget(self.hwid_ck)
        advanced_row.addStretch(1)
        identity_layout.addLayout(advanced_row)

        checks = QHBoxLayout()
        self.webrtc_ck = QCheckBox("Disable WebRTC")
        self.geo_ck = QCheckBox("Enable Geolocation")
        checks.addWidget(self.webrtc_ck)
        checks.addWidget(self.geo_ck)
        checks.addStretch(1)
        identity_layout.addLayout(checks)

        self.ua_ctrl = self._make_ua_control(identity_layout)
        layout.addWidget(identity_box)
        layout.addStretch(1)
        return self._scroll_tab(page)

    def _build_health_tab(self) -> QScrollArea:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        health_box = QGroupBox("Setup Health")
        health_layout = QVBoxLayout(health_box)
        self.health_label = QLabel()
        self.health_label.setWordWrap(True)
        self.health_label.setTextFormat(Qt.RichText)
        health_layout.addWidget(self.health_label)
        layout.addWidget(health_box)

        note = QLabel(
            "Health warnings are guidance only. They do not block saving and they do not guarantee that any website will allow or deny a browser session."
        )
        note.setWordWrap(True)
        set_widget_role(note, "sectionHint")
        layout.addWidget(note)
        layout.addStretch(1)
        return self._scroll_tab(page)

    def _connect_signals(self) -> None:
        self.use_proxy.stateChanged.connect(self._sync_proxy)
        self.auth_ck.stateChanged.connect(self._sync_proxy)
        self.apply_region_btn.clicked.connect(self._apply_region_profile_to_fields)
        self.region_cb.currentIndexChanged.connect(self._on_region_changed)
        self.launch_mode_cb.currentIndexChanged.connect(self._refresh_launch_mode_hint)
        self.save_btn.clicked.connect(self._save)
        self.cancel_btn.clicked.connect(self.reject)

        for widget in (
            self.use_proxy,
            self.auth_ck,
            self.ip_in,
            self.port_in,
            self.proto_cb,
            self.user_in,
            self.pass_in,
            self.region_cb,
            self.launch_mode_cb,
            self.webrtc_ck,
            self.geo_ck,
            self.hwid_ck,
            self.landing_in,
        ):
            self._connect_health_signal(widget)

    def _connect_health_signal(self, widget) -> None:
        if isinstance(widget, QLineEdit):
            widget.textChanged.connect(self._refresh_health)
            return
        if isinstance(widget, QComboBox):
            widget.currentIndexChanged.connect(self._refresh_health)
            return
        if isinstance(widget, QCheckBox):
            widget.stateChanged.connect(self._refresh_health)

    def _make_stack(self, label, items, parent_layout):
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        rb_default = QRadioButton("Preset")
        rb_custom = QRadioButton("Custom")
        rb_default.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(rb_default)
        group.addButton(rb_custom)

        radio_layout = QHBoxLayout()
        radio_layout.addWidget(rb_default)
        radio_layout.addWidget(rb_custom)
        radio_layout.addStretch(1)

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
        combo.currentIndexChanged.connect(self._refresh_health)
        line_edit.textChanged.connect(self._refresh_health)
        rb_default.toggled.connect(self._refresh_health)
        rb_custom.toggled.connect(self._refresh_health)

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
        self.ua_ctrl["latest_label"].setText(f'{latest["label"]}\n{latest["user_agent"]}')

    def _make_ua_control(self, parent_layout):
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        rb_random = QRadioButton("Random Real")
        rb_latest = QRadioButton("Latest Stable (Real)")
        rb_list = QRadioButton("Select Recent Real")
        rb_custom = QRadioButton("Custom")
        rb_random.setChecked(True)

        group = QButtonGroup(self)
        for button in (rb_random, rb_latest, rb_list, rb_custom):
            group.addButton(button)
            button.toggled.connect(self._refresh_health)

        top = QHBoxLayout()
        top.addWidget(rb_random)
        top.addWidget(rb_latest)
        top.addWidget(rb_list)
        top.addWidget(rb_custom)
        top.addStretch(1)

        stack = QStackedWidget()

        page_random = QWidget()
        random_layout = QVBoxLayout(page_random)
        random_layout.setContentsMargins(0, 0, 0, 0)
        random_label = QLabel("Uses a recent real desktop Chrome identity for your current OS family.")
        random_label.setWordWrap(True)
        set_widget_role(random_label, "sectionHint")
        random_layout.addWidget(random_label)
        stack.addWidget(page_random)

        page_latest = QWidget()
        latest_layout = QVBoxLayout(page_latest)
        latest_layout.setContentsMargins(0, 0, 0, 0)
        latest_label = QLabel()
        latest_label.setWordWrap(True)
        set_widget_role(latest_label, "sectionHint")
        latest_layout.addWidget(latest_label)
        stack.addWidget(page_latest)

        page_list = QWidget()
        list_layout = QVBoxLayout(page_list)
        list_layout.setContentsMargins(0, 0, 0, 0)
        combo = QComboBox()
        combo.currentIndexChanged.connect(self._refresh_health)
        list_layout.addWidget(combo)
        stack.addWidget(page_list)

        page_custom = QWidget()
        custom_layout = QVBoxLayout(page_custom)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        line_edit = QLineEdit()
        line_edit.textChanged.connect(self._refresh_health)
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
            self._refresh_health()

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
        self._refresh_health()

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

    def _value_from_stack(self, stack_info):
        return stack_info["cb"].currentText() if stack_info["rb_def"].isChecked() else stack_info["le"].text().strip()

    def _selected_region_key(self) -> str:
        return normalize_region_profile_key(self.region_cb.currentData())

    def _selected_launch_mode(self) -> str:
        return normalize_launch_mode(self.launch_mode_cb.currentData())

    def _set_region_profile(self, key: str) -> None:
        clean_key = normalize_region_profile_key(key)
        for index in range(self.region_cb.count()):
            if self.region_cb.itemData(index) == clean_key:
                self.region_cb.setCurrentIndex(index)
                return
        self.region_cb.setCurrentIndex(0)

    def _set_launch_mode(self, mode: str) -> None:
        clean_mode = normalize_launch_mode(mode)
        for index in range(self.launch_mode_cb.count()):
            if self.launch_mode_cb.itemData(index) == clean_mode:
                self.launch_mode_cb.setCurrentIndex(index)
                return
        self.launch_mode_cb.setCurrentIndex(0)


    def _on_region_changed(self) -> None:
        self._apply_region_profile_to_fields()

    def _apply_region_profile_to_fields(self) -> None:
        defaults = region_defaults_for_key(self._selected_region_key())
        if defaults["timezone"]:
            self._set_stack(self.tz_stack, defaults["timezone"], TIME_ZONES)
        if defaults["language"]:
            self._set_stack(self.lang_stack, defaults["language"], LANGUAGES)
        self._refresh_region_hint()
        self._refresh_health()

    def _refresh_region_hint(self) -> None:
        profile = get_region_profile(self._selected_region_key())
        if not profile:
            self.region_hint.setText("No region profile selected. Timezone and language will use your manual choices.")
            return
        self.region_hint.setText(
            f'Recommended for {profile["label"]}: {profile["timezone"]} • {profile["language"]}'
        )

    def _refresh_launch_mode_hint(self) -> None:
        text = self.launch_mode_cb.itemData(self.launch_mode_cb.currentIndex(), Qt.ToolTipRole) or ""
        self.launch_mode_hint.setText(str(text))

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
            self._refresh_region_hint()
            self._refresh_launch_mode_hint()
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
            self.proto_cb.setCurrentText(proxy.get("protocol", "HTTP"))
            self.auth_ck.setChecked(proxy.get("auth", False))
            if proxy.get("auth"):
                self.user_in.setText(proxy.get("user", ""))
                self.pass_in.setText(proxy.get("password", ""))

        if inst.get("hwid", {}).get("enabled"):
            self.hwid_ck.setChecked(True)

        identity = inst.get("identity", {})
        self._set_region_profile(identity.get("region_profile", ""))
        self._set_launch_mode(identity.get("launch_mode", "normal"))
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

        self._refresh_region_hint()
        self._refresh_launch_mode_hint()

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

    def _preview_instance(self) -> dict:
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

        return {
            "name": self.name_in.text().strip(),
            "proxy": proxy,
            "identity": {
                "region_profile": self._selected_region_key(),
                "launch_mode": self._selected_launch_mode(),
                "timezone": self._value_from_stack(self.tz_stack),
                "language": self._value_from_stack(self.lang_stack),
                "webrtc_disabled": self.webrtc_ck.isChecked(),
                "geolocation_enabled": self.geo_ck.isChecked(),
            },
        }

    def _refresh_health(self) -> None:
        if not hasattr(self, "health_label"):
            return

        health = build_browser_profile_health(self._preview_instance())
        title = html.escape(health["summary"])
        warnings = health.get("warnings", [])

        if warnings:
            items = "".join(f"<li>{html.escape(str(warning))}</li>" for warning in warnings)
            body = f"<b>{title}</b><ul>{items}</ul>"
        else:
            body = f"<b>{title}</b><br>No setup warnings right now."

        self.health_label.setText(body)

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

        name = validation.name or name
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
            timezone=self._value_from_stack(self.tz_stack),
            language=self._value_from_stack(self.lang_stack),
            webrtc_disabled=self.webrtc_ck.isChecked(),
            geolocation_enabled=self.geo_ck.isChecked(),
            custom_ua=browser_identity["custom_ua"],
            landing_page=self.landing_in.text().strip(),
            browser_identity_mode=browser_identity["mode"],
            browser_identity_preset=browser_identity["preset"],
            region_profile=self._selected_region_key(),
            launch_mode=self._selected_launch_mode(),
        )
        if not result:
            self._show_save_error(result.message or "The instance could not be saved.")
            return

        saved_name = result.name or name
        self.manager.save_instance_group(saved_name, self.group_cb.currentText() or "Unassigned")
        self.instanceSaved.emit(saved_name)
        self.accept()
