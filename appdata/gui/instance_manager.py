# appdata/gui/instance_manager.py
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QComboBox, QRadioButton, QButtonGroup, QStackedWidget,
    QWidget, QGroupBox, QFormLayout, QFrame
)
from PySide6.QtGui import QPalette, QColor, QFont
from appdata.logic.group_manager import GroupManagerLogic
from appdata.config.constants import TIME_ZONES, LANGUAGES, COMMON_USER_AGENTS
from appdata.config.style_constants import BACKGROUND_MAIN, TEXT_COLOR, GROUP_HOVER, ACCENT_COLOR

class GuiInstanceManager(QDialog):
    instanceSaved = Signal(str)
    def __init__(self, manager, instance_name, parent=None):
        super().__init__(parent)
        pal = self.palette()
        pal.setColor(QPalette.Window, QColor(BACKGROUND_MAIN))
        pal.setColor(QPalette.WindowText, QColor(TEXT_COLOR))
        pal.setColor(QPalette.Base, QColor(BACKGROUND_MAIN))
        pal.setColor(QPalette.Button, QColor(BACKGROUND_MAIN))
        pal.setColor(QPalette.ButtonText, QColor(TEXT_COLOR))
        self.setPalette(pal)
        self.setFont(QFont("Segoe UI", 11))
        self.setStyleSheet(f"""
            QDialog        {{ background:{BACKGROUND_MAIN}; }}
            QLabel         {{ color:{TEXT_COLOR}; }}
            QLineEdit      {{ background:{GROUP_HOVER}; color:{TEXT_COLOR}; border-radius:3px; padding:4px; }}
            QLineEdit:focus{{ border:1px solid {ACCENT_COLOR}; }}
            QComboBox      {{ background:{GROUP_HOVER}; color:{TEXT_COLOR}; border-radius:3px; padding:2px 4px; }}
            QPushButton    {{ background:{BACKGROUND_MAIN}; color:{TEXT_COLOR}; border:1px solid {GROUP_HOVER}; border-radius:4px; padding:6px 12px; }}
            QPushButton:hover{{ background:{GROUP_HOVER}; border:1px solid {ACCENT_COLOR}; }}
            QCheckBox      {{ color:{TEXT_COLOR}; }}
            QGroupBox:title{{ color:{TEXT_COLOR}; subcontrol-origin: margin; left:10px; padding:0 3px 0 3px; }}
        """)
        self.resize(650, 440)
        self.setModal(True)
        self.manager = manager
        self.instance_name = instance_name
        self.setWindowTitle("Instance Manager")
        main = QVBoxLayout(self); main.setContentsMargins(15,15,15,15); main.setSpacing(12)
        head = QLabel("Manage Instance"); head.setFont(QFont("Segoe UI",13,QFont.Bold)); head.setAlignment(Qt.AlignHCenter); main.addWidget(head)
        main.addWidget(QLabel("Configure proxy, identity, landing page and user‑agent.", wordWrap=True))
        ln = QFrame(); ln.setFrameShape(QFrame.HLine); ln.setFrameShadow(QFrame.Sunken); main.addWidget(ln)
        basic = QGroupBox("Basic Info"); bf = QFormLayout(basic)
        self.name_in = QLineEdit()
        self.group_cb = QComboBox(); self.group_cb.addItems(GroupManagerLogic().get_all_groups())
        self.landing_in = QLineEdit("https://www.duckduckgo.com")
        bf.addRow(QLabel("Instance Name:"), self.name_in); bf.addRow(QLabel("Group:"), self.group_cb); bf.addRow(QLabel("Landing Page:"), self.landing_in); main.addWidget(basic)
        proxy_box = QGroupBox("Proxy Settings"); proxy_l = QVBoxLayout(proxy_box)
        self.use_proxy = QCheckBox("Use Proxy"); proxy_l.addWidget(self.use_proxy)
        pf = QFormLayout(); self.ip_in=QLineEdit(); self.port_in=QLineEdit(); self.proto_cb=QComboBox(); self.proto_cb.addItems(["HTTP","HTTPS","SOCKS4","SOCKS5"])
        self.auth_ck=QCheckBox("Require Authentication"); self.user_in=QLineEdit(); self.pass_in=QLineEdit()
        pf.addRow(QLabel("IP:"),self.ip_in); pf.addRow(QLabel("Port:"),self.port_in); pf.addRow(QLabel("Protocol:"),self.proto_cb); pf.addRow(self.auth_ck,QLabel(""))
        pf.addRow(QLabel("Username:"),self.user_in); pf.addRow(QLabel("Password:"),self.pass_in); proxy_l.addLayout(pf); main.addWidget(proxy_box)
        id_box = QGroupBox("Identity & Fingerprint"); idl = QVBoxLayout(id_box)
        adv = QHBoxLayout(); self.hwid_ck=QCheckBox("Use Random HWID"); self.anti_ck=QCheckBox("Antidetection"); adv.addWidget(self.hwid_ck); adv.addWidget(self.anti_ck); idl.addLayout(adv)
        self.tz_stack = self._make_stack("Time Zone:", TIME_ZONES, idl)
        self.lang_stack = self._make_stack("Language:", LANGUAGES, idl)
        chk = QHBoxLayout(); self.webrtc_ck=QCheckBox("Disable WebRTC"); self.geo_ck=QCheckBox("Enable Geolocation"); chk.addWidget(self.webrtc_ck); chk.addWidget(self.geo_ck); idl.addLayout(chk)
        self.ua_ctrl = self._make_ua_control(idl); main.addWidget(id_box)
        btns = QHBoxLayout(); self.save_btn=QPushButton("Save"); self.cancel_btn=QPushButton("Cancel"); btns.addWidget(self.save_btn); btns.addWidget(self.cancel_btn); main.addLayout(btns)
        self.use_proxy.stateChanged.connect(self._sync_proxy); self.auth_ck.stateChanged.connect(self._sync_proxy)
        self.save_btn.clicked.connect(self._save); self.cancel_btn.clicked.connect(self.reject)
        self._sync_proxy(); self._load_existing()
    def _make_stack(self,label,items,parent_layout):
        fm=QFormLayout(); rb_def=QRadioButton("Default"); rb_cus=QRadioButton("Custom"); rb_def.setChecked(True); grp=QButtonGroup(self); grp.addButton(rb_def); grp.addButton(rb_cus)
        rb_lay=QHBoxLayout(); rb_lay.addWidget(rb_def); rb_lay.addWidget(rb_cus); stack=QStackedWidget()
        pg_combo=QWidget(); lc=QVBoxLayout(pg_combo); cb=QComboBox(); cb.addItems(items); lc.addWidget(cb)
        pg_cus=QWidget(); lc2=QVBoxLayout(pg_cus); le=QLineEdit(); lc2.addWidget(le); stack.addWidget(pg_combo); stack.addWidget(pg_cus)
        rb_def.toggled.connect(lambda: stack.setCurrentIndex(0 if rb_def.isChecked() else 1))
        fm.addRow(QLabel(label),rb_lay); fm.addRow(QLabel(""),stack); parent_layout.addLayout(fm)
        return dict(rb_def=rb_def,cb=cb,le=le,stack=stack)
    def _make_ua_control(self,parent_layout):
        fm=QFormLayout(); rb_rand=QRadioButton("Random"); rb_list=QRadioButton("Select"); rb_cust=QRadioButton("Custom"); rb_rand.setChecked(True)
        grp=QButtonGroup(self); grp.addButton(rb_rand); grp.addButton(rb_list); grp.addButton(rb_cust); top=QHBoxLayout(); top.addWidget(rb_rand); top.addWidget(rb_list); top.addWidget(rb_cust)
        stack=QStackedWidget(); stack.addWidget(QWidget())
        pg_list=QWidget(); l1=QVBoxLayout(pg_list); cb=QComboBox(); cb.addItems(COMMON_USER_AGENTS); l1.addWidget(cb); stack.addWidget(pg_list)
        pg_cus=QWidget(); l2=QVBoxLayout(pg_cus); le=QLineEdit(); l2.addWidget(le); stack.addWidget(pg_cus)
        def sync(): stack.setCurrentIndex(0 if rb_rand.isChecked() else 1 if rb_list.isChecked() else 2)
        rb_rand.toggled.connect(sync); rb_list.toggled.connect(sync); rb_cust.toggled.connect(sync); sync()
        fm.addRow(QLabel("User Agent:"),top); fm.addRow(QLabel(""),stack); parent_layout.addLayout(fm)
        return dict(rb_rand=rb_rand,rb_list=rb_list,rb_cust=rb_cust,cb=cb,le=le,stack=stack)
    def _sync_proxy(self):
        en=self.use_proxy.isChecked()
        for w in (self.ip_in,self.port_in,self.proto_cb,self.auth_ck): w.setEnabled(en)
        auth_en=en and self.auth_ck.isChecked()
        for w in (self.user_in,self.pass_in): w.setEnabled(auth_en)
    def _select_group(self,name):
        idx=self.group_cb.findText(name,Qt.MatchFixedString)
        if idx==-1: self.group_cb.addItem(name); idx=self.group_cb.count()-1
        self.group_cb.setCurrentIndex(idx)
    def _load_existing(self):
        if not self.instance_name: self._select_group("Unassigned"); return
        inst=self.manager.get_instance(self.instance_name) or {}
        self.name_in.setText(inst.get("name",""))
        self._select_group(inst.get("group","Unassigned"))
        self.landing_in.setText(inst.get("landing_page","https://www.duckduckgo.com"))
        if (px:=inst.get("proxy")):
            self.use_proxy.setChecked(True); self.ip_in.setText(px.get("ip","")); self.port_in.setText(px.get("port","")); self.proto_cb.setCurrentText(px.get("protocol","")); self.auth_ck.setChecked(px.get("auth",False))
            if px.get("auth"): self.user_in.setText(px.get("user","")); self.pass_in.setText(px.get("password",""))
        if inst.get("hwid",{}).get("enabled"): self.hwid_ck.setChecked(True)
        if inst.get("antidetect",{}).get("enabled"): self.anti_ck.setChecked(True)
        ident=inst.get("identity",{}); self._set_stack(self.tz_stack,ident.get("timezone"),TIME_ZONES); self._set_stack(self.lang_stack,ident.get("language"),LANGUAGES)
        cu=ident.get("custom_user_agent"); 
        if cu=="": self.ua_ctrl["rb_rand"].setChecked(True)
        elif cu in COMMON_USER_AGENTS: self.ua_ctrl["rb_list"].setChecked(True); self.ua_ctrl["cb"].setCurrentText(cu)
        elif cu is not None: self.ua_ctrl["rb_cust"].setChecked(True); self.ua_ctrl["le"].setText(cu)
        if ident.get("webrtc_disabled"): self.webrtc_ck.setChecked(True)
        if ident.get("geolocation_enabled"): self.geo_ck.setChecked(True)
    def _set_stack(self,st,val,pool):
        if not val: return
        if val in pool: st["rb_def"].setChecked(True); st["cb"].setCurrentText(val)
        else: st["rb_def"].setChecked(False); st["le"].setText(val)
    def _save(self):
        name=self.name_in.text().strip(); px=None
        if self.use_proxy.isChecked(): px=dict(ip=self.ip_in.text().strip(),port=self.port_in.text().strip(),protocol=self.proto_cb.currentText(),auth=self.auth_ck.isChecked(),user=self.user_in.text().strip(),password=self.pass_in.text().strip())
        def val_from(st): return st["cb"].currentText() if st["rb_def"].isChecked() else st["le"].text().strip()
        if self.ua_ctrl["rb_rand"].isChecked(): cu="" 
        elif self.ua_ctrl["rb_list"].isChecked(): cu=self.ua_ctrl["cb"].currentText() 
        else: cu=self.ua_ctrl["le"].text().strip()
        self.manager.save_instance_extended(old_name=self.instance_name,new_name=name,proxy_enabled=bool(px),ip=px["ip"] if px else "",port=px["port"] if px else "",protocol=px["protocol"] if px else "",auth_enabled=px["auth"] if px else False,user=px["user"] if px else "",password=px["password"] if px else "",hwid_enabled=self.hwid_ck.isChecked(),antidetect_enabled=self.anti_ck.isChecked(),timezone=val_from(self.tz_stack),language=val_from(self.lang_stack),webrtc_disabled=self.webrtc_ck.isChecked(),geolocation_enabled=self.geo_ck.isChecked(),custom_ua=cu,landing_page=self.landing_in.text().strip())
        self.manager.save_instance_group(name,self.group_cb.currentText() or "Unassigned"); self.instanceSaved.emit(name); self.accept()
