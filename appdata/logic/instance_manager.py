# appdata/logic/instance_manager.py
import os, string, random, concurrent.futures, copy
from typing import List, Dict
from PySide6.QtCore import QObject, Signal
from appdata.logic.browser_manager import BrowserManager
from appdata.logic.config_handler import ConfigHandler
from appdata.logic.proxy_tester import ProxyTester
from appdata.utils.io_helpers import safe_json_read, safe_json_write


class LogicInstanceManager(QObject):
    statusChanged = Signal()
    proxyTested = Signal(str, bool)

    def __init__(self):
        super().__init__()
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() * 2)
        self.browser = BrowserManager()
        self.tester = ProxyTester()
        self.tester.result.connect(self._on_proxy_result)
        cfg = ConfigHandler()
        self.path = os.path.join(cfg.user_folder, "Jivaro", "Instanciar", "config")
        self.instances_file = os.path.join(self.path, "instances.json")
        self.data: List[Dict] = []
        self.load()

    def _on_proxy_result(self, name, ok):
        inst = self.get_instance(name)
        if inst:
            inst["proxy_ok"] = ok
            self.save()
            self.proxyTested.emit(name, ok)

    def _kick_proxy_test(self, inst):
        px = inst.get("proxy") or {}
        if px.get("ip") and px.get("port"):
            self.tester.test(inst["name"], px["ip"], px["port"])

    def load(self):
        self.data = safe_json_read(self.instances_file, [])
        changed = False
        for inst in self.data:
            if not inst.get("group"):
                inst["group"] = "Unassigned"
                changed = True
            self._kick_proxy_test(inst)
        if changed:
            self.save()

    def save(self):
        safe_json_write(self.instances_file, self.data)

    def get_instance(self, name):
        return next((i for i in self.data if i["name"] == name), None)

    def _unique_name(self, base):
        n, c = base, 1
        while any(i["name"] == n for i in self.data):
            n = f"{base} ({c})"
            c += 1
        return n

    def duplicate_instance(self, name):
        src = self.get_instance(name)
        if not src:
            return
        dup = copy.deepcopy(src)
        dup["name"] = self._unique_name(f"{name} Copy")
        dup["folder_id"] = "".join(random.choices(string.ascii_letters + string.digits, k=20))
        self.data.append(dup)
        self.save()
        self._kick_proxy_test(dup)
        self.statusChanged.emit()

    def save_instance(self, old_name, new_name, proxy_enabled, ip, port, protocol, auth_enabled, user, password):
        if old_name:
            existing = self.get_instance(old_name)
            if not existing or (old_name != new_name and any(x["name"] == new_name for x in self.data)):
                return
            existing["name"] = new_name
            existing["proxy"] = (
                {
                    "ip": ip,
                    "port": port,
                    "protocol": protocol,
                    "auth": auth_enabled,
                    "user": user,
                    "password": password,
                }
                if proxy_enabled
                else None
            )
            self._kick_proxy_test(existing)
        else:
            if any(x["name"] == new_name for x in self.data):
                return
            folder_id = "".join(random.choices(string.ascii_letters + string.digits, k=20))
            inst = {
                "name": new_name,
                "folder_id": folder_id,
                "proxy": (
                    {
                        "ip": ip,
                        "port": port,
                        "protocol": protocol,
                        "auth": auth_enabled,
                        "user": user,
                        "password": password,
                    }
                    if proxy_enabled
                    else None
                ),
                "group": "Unassigned",
            }
            self.data.append(inst)
            self._kick_proxy_test(inst)
        self.save()
        self.statusChanged.emit()

    def delete_instance(self, name):
        self.data = [i for i in self.data if i["name"] != name]
        self.save()
        self.statusChanged.emit()

    def rearrange_group_instances(self, group_name: str, ordered_names: List[str]):
        lookup = {i["name"]: i for i in self.data if i.get("group") == group_name}
        if not lookup:
            return
        first_index = next(i for i, inst in enumerate(self.data) if inst.get("group") == group_name)
        self.data = [inst for inst in self.data if inst.get("group") != group_name]
        ordered_instances = [lookup[n] for n in ordered_names if n in lookup]
        for idx, inst in enumerate(ordered_instances):
            self.data.insert(first_index + idx, inst)
        self.save()
        self.statusChanged.emit()

    def save_instance_group(self, instance_name, group_name):
        inst = self.get_instance(instance_name)
        if inst:
            inst["group"] = group_name or "Unassigned"
            self.save()
            self.statusChanged.emit()

    def launch_instance(self, name):
        inst = self.get_instance(name)
        if inst:
            self.pool.submit(self.browser.launch, inst)

    def save_instance_extended(
        self,
        old_name,
        new_name,
        proxy_enabled,
        ip,
        port,
        protocol,
        auth_enabled,
        user,
        password,
        hwid_enabled,
        antidetect_enabled,
        timezone,
        language,
        webrtc_disabled,
        geolocation_enabled,
        custom_ua,
        landing_page,
    ):
        self.save_instance(
            old_name,
            new_name,
            proxy_enabled,
            ip,
            port,
            protocol,
            auth_enabled,
            user,
            password,
        )
        inst = self.get_instance(new_name)
        if not inst:
            return
        inst["landing_page"] = landing_page or "https://www.duckduckgo.com"
        inst.setdefault("hwid", {})["enabled"] = hwid_enabled
        inst.setdefault("antidetect", {})["enabled"] = antidetect_enabled
        ident = inst.setdefault("identity", {})
        ident["timezone"] = timezone
        ident["language"] = language
        ident["webrtc_disabled"] = webrtc_disabled
        ident["geolocation_enabled"] = geolocation_enabled
        ident["custom_user_agent"] = custom_ua
        self.save()
        self.statusChanged.emit()
