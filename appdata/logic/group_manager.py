# appdata/logic/group_manager.py
import os
from typing import List
from appdata.logic.config_handler import ConfigHandler
from appdata.logic.instance_manager import LogicInstanceManager
from appdata.utils.io_helpers import safe_json_read, safe_json_write

class GroupManagerLogic:
    def __init__(self):
        self.config = ConfigHandler()
        self.path = os.path.join(self.config.user_folder, "Jivaro", "Instanciar", "config")
        self.groups_file = os.path.join(self.path, "groups.json")
        self.instance_logic = LogicInstanceManager()
        self.groups_data: List[dict] = []
        self.load_groups()

    def load_groups(self):
        self.groups_data = safe_json_read(self.groups_file, [])
        if not any(g["name"] == "Unassigned" for g in self.groups_data):
            self.groups_data.append({"name": "Unassigned"})
            self.save_groups()

    def save_groups(self):
        safe_json_write(self.groups_file, self.groups_data)

    def get_group(self, name): return next((g for g in self.groups_data if g["name"] == name), None)
    def get_all_groups(self): return [g["name"] for g in self.groups_data]

    def create_group(self, name):
        name = name.strip()
        if name and not any(g["name"].lower() == name.lower() for g in self.groups_data):
            self.groups_data.append({"name": name})
            self.save_groups()

    def edit_group(self, old_name, new_name):
        old_name, new_name = old_name.strip(), new_name.strip()
        if old_name.lower() == "unassigned" or not new_name or new_name.lower() == "unassigned": return
        if any(g["name"].lower() == new_name.lower() for g in self.groups_data): return
        grp = self.get_group(old_name)
        if not grp: return
        grp["name"] = new_name
        self.save_groups()
        for inst in self.instance_logic.data:
            if inst.get("group", "Unassigned") == old_name:
                inst["group"] = new_name
        self.instance_logic.save()

    def delete_group(self, name):
        self.groups_data = [g for g in self.groups_data if g["name"].lower() != name.lower()]
        self.save_groups()
        for inst in self.instance_logic.data:
            if inst.get("group", "Unassigned").lower() == name.lower():
                inst["group"] = "Unassigned"
        self.instance_logic.save()

    def reorder_groups(self, new_order):
        ordered = [self.get_group(n) for n in new_order if self.get_group(n)]
        remaining = [g for g in self.groups_data if g["name"] not in new_order]
        self.groups_data = ordered + remaining
        self.save_groups()
