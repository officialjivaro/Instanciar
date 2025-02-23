# appdata/gui/instance_editor.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

class GuiInstanceManager(QDialog):
    def __init__(self, manager, instance_name, parent=None):
        super().__init__(parent)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(50, 50, 50))
        palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
        self.setPalette(palette)
        self.setModal(True)
        self.manager = manager
        self.instance_name = instance_name
        self.setWindowTitle("Instance Editor")
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
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
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
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(button_layout)
        self.use_proxy_checkbox.stateChanged.connect(self.on_proxy_checkbox_changed)
        self.proxy_auth_checkbox.stateChanged.connect(self.on_proxy_auth_checkbox_changed)
        self.save_button.clicked.connect(self.save)
        self.cancel_button.clicked.connect(self.reject)
        self.load_existing()
        self.apply_current_states()

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

    def load_existing(self):
        if self.instance_name:
            instance = self.manager.get_instance(self.instance_name)
            if instance:
                self.name_input.setText(instance["name"])
                if instance["proxy"]:
                    self.use_proxy_checkbox.setChecked(True)
                    self.proxy_ip_input.setText(instance["proxy"]["ip"])
                    self.proxy_port_input.setText(instance["proxy"]["port"])
                    if instance["proxy"]["protocol"] in ["HTTP", "HTTPS", "SOCKS4", "SOCKS5"]:
                        index = self.proxy_protocol_combo.findText(instance["proxy"]["protocol"])
                        if index >= 0:
                            self.proxy_protocol_combo.setCurrentIndex(index)
                    if instance["proxy"]["auth"]:
                        self.proxy_auth_checkbox.setChecked(True)
                        self.proxy_user_input.setText(instance["proxy"]["user"])
                        self.proxy_pass_input.setText(instance["proxy"]["password"])
                if "hwid" in instance and instance["hwid"]["enabled"]:
                    self.hwid_checkbox.setChecked(True)

    def save(self):
        name = self.name_input.text()
        proxy_enabled = self.use_proxy_checkbox.isChecked()
        ip = self.proxy_ip_input.text()
        port = self.proxy_port_input.text()
        protocol = self.proxy_protocol_combo.currentText()
        auth_enabled = self.proxy_auth_checkbox.isChecked()
        user = self.proxy_user_input.text()
        password = self.proxy_pass_input.text()
        hwid_enabled = self.hwid_checkbox.isChecked()
        self.manager.save_instance_hwid(self.instance_name, name, proxy_enabled, ip, port, protocol, auth_enabled, user, password, hwid_enabled)
        self.accept()
