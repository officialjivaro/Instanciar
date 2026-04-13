# appdata/logic/instance_manager.py
import concurrent.futures
import copy
import os
import random
import string
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from PySide6.QtCore import QObject, Signal

from appdata.logic.browser_manager import BrowserManager
from appdata.logic.config_handler import ConfigHandler
from appdata.logic.proxy_tester import ProxyTester
from appdata.utils.browser_identity import normalize_identity_selection
from appdata.utils.io_helpers import safe_json_read, safe_json_write


@dataclass
class SaveResult:
    """Simple save result object that is truthy on success and falsey on failure."""
    ok: bool
    message: str = ""
    name: str = ""

    def __bool__(self):
        return self.ok


class LogicInstanceManager(QObject):
    statusChanged = Signal()
    proxyTested = Signal(str, bool)

    def __init__(self):
        super().__init__()
        max_workers = max(2, (os.cpu_count() or 1) * 2)
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.browser = BrowserManager()
        self.tester = ProxyTester()
        self.tester.result.connect(self._on_proxy_result)

        # Keep the latest in-flight proxy test token per instance name so an old
        # result cannot overwrite a newer test after the user edits proxy settings.
        self._pending_proxy_tests = {}

        cfg = ConfigHandler()
        self.path = os.path.join(cfg.user_folder, "Jivaro", "Instanciar", "config")
        self.instances_file = os.path.join(self.path, "instances.json")
        self.data: List[Dict] = []
        self.load()

    def _result(self, ok: bool, message: str = "", name: str = "") -> SaveResult:
        return SaveResult(ok=ok, message=message, name=name)

    def _proxy_is_configured(self, inst: Dict) -> bool:
        proxy = inst.get("proxy") or {}
        return bool(str(proxy.get("ip") or "").strip() and str(proxy.get("port") or "").strip())

    def _proxy_timestamp(self) -> str:
        return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")

    def _set_proxy_test_pending(self, inst: Dict):
        inst["proxy_ok"] = None
        inst["proxy_test"] = {
            "ok": None,
            "checked_at": "",
            "reason": "",
        }

    def _clear_proxy_test_data(self, inst: Dict):
        inst["proxy_ok"] = None
        inst.pop("proxy_test", None)

    def _normalize_proxy_test_schema(self, inst: Dict) -> bool:
        changed = False

        if not self._proxy_is_configured(inst):
            if inst.get("proxy_ok") is not None:
                inst["proxy_ok"] = None
                changed = True
            if "proxy_test" in inst:
                inst.pop("proxy_test", None)
                changed = True
            return changed

        legacy_ok = inst.get("proxy_ok")
        proxy_test = inst.get("proxy_test")

        if not isinstance(proxy_test, dict):
            inst["proxy_test"] = {
                "ok": legacy_ok if isinstance(legacy_ok, bool) else None,
                "checked_at": "",
                "reason": "",
            }
            proxy_test = inst["proxy_test"]
            changed = True

        if proxy_test.get("ok") not in (True, False, None):
            proxy_test["ok"] = legacy_ok if isinstance(legacy_ok, bool) else None
            changed = True

        if "checked_at" not in proxy_test or proxy_test.get("checked_at") is None:
            proxy_test["checked_at"] = ""
            changed = True

        if "reason" not in proxy_test or proxy_test.get("reason") is None:
            proxy_test["reason"] = ""
            changed = True

        if inst.get("proxy_ok") != proxy_test.get("ok"):
            inst["proxy_ok"] = proxy_test.get("ok")
            changed = True

        return changed

    def _on_proxy_result(self, name, request_id, ok, reason):
        pending_request_id = self._pending_proxy_tests.get(name)
        if pending_request_id != request_id:
            return

        inst = self.get_instance(name)
        self._pending_proxy_tests.pop(name, None)

        # Ignore late results for instances that were deleted, renamed, or had the
        # proxy removed after the test was started.
        if not inst or not self._proxy_is_configured(inst):
            return

        inst["proxy_ok"] = ok
        inst["proxy_test"] = {
            "ok": ok,
            "checked_at": self._proxy_timestamp(),
            "reason": reason or "",
        }
        self.save()
        self.proxyTested.emit(name, ok)

    def _kick_proxy_test(self, inst):
        proxy = inst.get("proxy") or {}
        if not proxy.get("ip") or not proxy.get("port"):
            self._pending_proxy_tests.pop(inst.get("name", ""), None)
            return

        request_id = uuid.uuid4().hex
        self._pending_proxy_tests[inst["name"]] = request_id
        self.tester.test(
            inst["name"],
            request_id,
            proxy.get("ip", ""),
            proxy.get("port", ""),
            proxy.get("protocol", "HTTP"),
            proxy.get("auth", False),
            proxy.get("user", ""),
            proxy.get("password", ""),
        )

    def validate_instance_inputs(
        self,
        old_name,
        new_name,
        proxy_enabled,
        ip,
        port,
        auth_enabled,
        user,
        password,
    ) -> SaveResult:
        """
        Validate the fields used by the save flow.

        The GUI uses this for quick user feedback, and the save methods use
        it again as a final safety check before mutating data.
        """
        name = (new_name or "").strip()

        if not name:
            return self._result(False, "Instance name cannot be blank.")

        if old_name:
            existing = self.get_instance(old_name)
            if not existing:
                return self._result(False, "The instance you are editing could not be found.", name=name)
            if old_name != name and any(item["name"] == name for item in self.data):
                return self._result(False, f'An instance named "{name}" already exists.', name=name)
        else:
            if any(item["name"] == name for item in self.data):
                return self._result(False, f'An instance named "{name}" already exists.', name=name)

        if proxy_enabled:
            host = (ip or "").strip()
            port_text = (port or "").strip()
            username = (user or "").strip()
            proxy_password = (password or "").strip()

            if not host:
                return self._result(False, "Proxy IP/host is required when Use Proxy is enabled.", name=name)

            if not port_text:
                return self._result(False, "Proxy port is required when Use Proxy is enabled.", name=name)

            if not port_text.isdigit():
                return self._result(False, "Proxy port must be a whole number between 1 and 65535.", name=name)

            port_value = int(port_text)
            if port_value < 1 or port_value > 65535:
                return self._result(False, "Proxy port must be between 1 and 65535.", name=name)

            if auth_enabled:
                if not username:
                    return self._result(False, "Proxy username is required when authentication is enabled.", name=name)
                if not proxy_password:
                    return self._result(False, "Proxy password is required when authentication is enabled.", name=name)

        return self._result(True, name=name)

    def _normalize_identity_schema(self, inst: Dict) -> bool:
        identity = inst.get("identity")
        if not isinstance(identity, dict):
            return False

        normalized = normalize_identity_selection(identity)
        changed = False
        if identity.get("browser_identity_mode") != normalized["mode"]:
            identity["browser_identity_mode"] = normalized["mode"]
            changed = True
        if identity.get("browser_identity_preset") != normalized["preset_key"]:
            identity["browser_identity_preset"] = normalized["preset_key"]
            changed = True

        custom_ua = normalized["custom_user_agent"]
        if custom_ua is not None and identity.get("custom_user_agent") != custom_ua:
            identity["custom_user_agent"] = custom_ua
            changed = True

        return changed

    def load(self):
        self.data = safe_json_read(self.instances_file, [])
        changed = False
        for inst in self.data:
            if not inst.get("group"):
                inst["group"] = "Unassigned"
                changed = True
            if self._normalize_identity_schema(inst):
                changed = True
            if self._normalize_proxy_test_schema(inst):
                changed = True
            self._kick_proxy_test(inst)
        if changed:
            self.save()

    def save(self):
        safe_json_write(self.instances_file, self.data)

    def get_instance(self, name):
        return next((item for item in self.data if item["name"] == name), None)

    def _unique_name(self, base):
        name, count = base, 1
        while any(item["name"] == name for item in self.data):
            name = f"{base} ({count})"
            count += 1
        return name

    def duplicate_instance(self, name):
        src = self.get_instance(name)
        if not src:
            return

        dup = copy.deepcopy(src)
        dup["name"] = self._unique_name(f"{name} Copy")
        dup["folder_id"] = "".join(random.choices(string.ascii_letters + string.digits, k=20))

        if self._proxy_is_configured(dup):
            self._set_proxy_test_pending(dup)
        else:
            self._clear_proxy_test_data(dup)

        self.data.append(dup)
        self.save()
        self._kick_proxy_test(dup)
        self.statusChanged.emit()

    def save_instance(self, old_name, new_name, proxy_enabled, ip, port, protocol, auth_enabled, user, password):
        validation = self.validate_instance_inputs(
            old_name=old_name,
            new_name=new_name,
            proxy_enabled=proxy_enabled,
            ip=ip,
            port=port,
            auth_enabled=auth_enabled,
            user=user,
            password=password,
        )
        if not validation:
            return validation

        new_name = validation.name
        ip = (ip or "").strip()
        port = (port or "").strip()
        user = (user or "").strip()
        password = (password or "").strip()

        proxy_data = (
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

        if old_name:
            existing = self.get_instance(old_name)
            if not existing:
                return self._result(False, "The instance you are editing could not be found.", name=new_name)

            if old_name != new_name:
                self._pending_proxy_tests.pop(old_name, None)

            existing["name"] = new_name
            existing["proxy"] = proxy_data

            if proxy_data:
                self._set_proxy_test_pending(existing)
                self._kick_proxy_test(existing)
            else:
                self._clear_proxy_test_data(existing)
                self._pending_proxy_tests.pop(new_name, None)
        else:
            folder_id = "".join(random.choices(string.ascii_letters + string.digits, k=20))
            inst = {
                "name": new_name,
                "folder_id": folder_id,
                "proxy": proxy_data,
                "group": "Unassigned",
            }

            if proxy_data:
                self._set_proxy_test_pending(inst)
            else:
                self._clear_proxy_test_data(inst)

            self.data.append(inst)
            self._kick_proxy_test(inst)

        self.save()
        self.statusChanged.emit()
        return self._result(True, name=new_name)

    def delete_instance(self, name):
        self._pending_proxy_tests.pop(name, None)
        self.data = [item for item in self.data if item["name"] != name]
        self.save()
        self.statusChanged.emit()

    def rearrange_group_instances(self, group_name: str, ordered_names: List[str]):
        lookup = {item["name"]: item for item in self.data if item.get("group") == group_name}
        if not lookup:
            return

        first_index = next(i for i, inst in enumerate(self.data) if inst.get("group") == group_name)
        self.data = [inst for inst in self.data if inst.get("group") != group_name]
        ordered_instances = [lookup[name] for name in ordered_names if name in lookup]
        for index, inst in enumerate(ordered_instances):
            self.data.insert(first_index + index, inst)

        self.save()
        self.statusChanged.emit()

    def save_instance_group(self, instance_name, group_name):
        inst = self.get_instance(instance_name)
        if inst:
            inst["group"] = group_name or "Unassigned"
            self.save()
            self.statusChanged.emit()

    def _launch_task(self, inst):
        result = self.browser.launch(inst)

        # Keep launch results structured so the UI can tell the difference
        # between a clean start and a start with privacy warnings.
        if result is None:
            return {
                "started": True,
                "privacy_ok": True,
                "warnings": [],
                "steps": {},
                "step_errors": {},
            }
        return result

    def launch_instance(self, name):
        inst = self.get_instance(name)
        if not inst:
            return None
        return self.pool.submit(self._launch_task, copy.deepcopy(inst))

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
        browser_identity_mode,
        browser_identity_preset,
    ):
        base_result = self.save_instance(
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
        if not base_result:
            return base_result

        inst = self.get_instance(base_result.name)
        if not inst:
            return self._result(False, "The instance could not be found after saving.", name=base_result.name)

        inst["landing_page"] = landing_page or "https://www.duckduckgo.com"
        inst.setdefault("hwid", {})["enabled"] = hwid_enabled
        inst.setdefault("antidetect", {})["enabled"] = antidetect_enabled

        identity = inst.setdefault("identity", {})
        identity["timezone"] = timezone
        identity["language"] = language
        identity["webrtc_disabled"] = webrtc_disabled
        identity["geolocation_enabled"] = geolocation_enabled
        identity["custom_user_agent"] = custom_ua
        identity["browser_identity_mode"] = browser_identity_mode
        identity["browser_identity_preset"] = browser_identity_preset

        self.save()
        self.statusChanged.emit()
        return self._result(True, name=base_result.name)