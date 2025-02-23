# appdata/logic/instance_manager.py
import os
import json
import string
import random
from appdata.logic.browser_manager import BrowserManager
from appdata.logic.config_handler import ConfigHandler

class LogicInstanceManager:
    def __init__(self):
        self.browser = BrowserManager()
        self.config = ConfigHandler()
        self.path = os.path.join(self.config.user_folder, "Jivaro", "Instanciar", "config")
        self.instances_file = os.path.join(self.path, "instances.json")
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        if not os.path.exists(self.instances_file):
            with open(self.instances_file, "w", encoding="utf-8") as f:
                f.write("[]")
        self.load()

    def load(self):
        with open(self.instances_file, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def save(self):
        with open(self.instances_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    def get_instance(self, name):
        for i in self.data:
            if i["name"] == name:
                return i

    def save_instance(self, old_name, new_name, proxy_enabled, ip, port, protocol, auth_enabled, user, password):
        if old_name is not None:
            existing = self.get_instance(old_name)
            if existing:
                if old_name != new_name:
                    for x in self.data:
                        if x["name"] == new_name:
                            return
                existing["name"] = new_name
                if proxy_enabled:
                    existing["proxy"] = {
                        "ip": ip,
                        "port": port,
                        "protocol": protocol,
                        "auth": auth_enabled,
                        "user": user,
                        "password": password
                    }
                else:
                    existing["proxy"] = None
            else:
                return
        else:
            for x in self.data:
                if x["name"] == new_name:
                    return
            folder_id = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
            entry = {
                "name": new_name,
                "folder_id": folder_id,
                "proxy": None
            }
            if proxy_enabled:
                entry["proxy"] = {
                    "ip": ip,
                    "port": port,
                    "protocol": protocol,
                    "auth": auth_enabled,
                    "user": user,
                    "password": password
                }
            self.data.append(entry)
        self.save()

    def delete_instance(self, name):
        self.data = [i for i in self.data if i["name"] != name]
        self.save()

    def rearrange_instances(self, order):
        ordered = []
        for n in order:
            for i in self.data:
                if i["name"] == n:
                    ordered.append(i)
                    break
        self.data = ordered
        self.save()

    def save_instance_hwid(self, old_name, new_name, proxy_enabled, ip, port, protocol, auth_enabled, user, password, hwid_enabled):
        self.save_instance(old_name, new_name, proxy_enabled, ip, port, protocol, auth_enabled, user, password)
        inst = self.get_instance(new_name)
        if not inst:
            return
        if "folder_id" not in inst:
            return
        if "hwid" not in inst:
            inst["hwid"] = {}
        inst["hwid"]["enabled"] = hwid_enabled
        self.save()

    def launch_instance(self, name, browser_name, should_block):
        inst = self.get_instance(name)
        if inst:
            self.browser.launch(inst, browser_name, should_block)
