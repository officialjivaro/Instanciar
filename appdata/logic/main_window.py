# appdata/logic/main_window.py
import webbrowser
from concurrent.futures import Future

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont, QColor, QBrush
from PySide6.QtWidgets import QTreeWidgetItem, QMessageBox

from appdata.gui.instance_manager import GuiInstanceManager
from appdata.gui.group_manager import GuiGroupManager
from appdata.logic.group_manager import GroupManagerLogic
from appdata.config.style_constants import (
    GROUP_DEFAULT,
    INSTANCE_DEFAULT,
    TEXT_COLOR,
    FONT_FAMILY,
    FONT_SIZE,
    ACCENT_COLOR,
)


class MainWindowLogic(QObject):
    """Main-window controller for tree actions, dialogs, and status feedback."""

    toastRequested = Signal(str, str)

    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.group_logic = GroupManagerLogic()
        self.manager.proxyTested.connect(self._on_proxy_tested)
        self._tree = None

    def _is_reserved_group(self, name):
        return (name or "").strip().casefold() == "unassigned"

    def _make_group_item(self, tree, name):
        is_default = self._is_reserved_group(name)

        item = QTreeWidgetItem([name, ""])
        item.setData(0, Qt.UserRole, {"type": "group", "name": name, "is_default": is_default})

        for column in (0, 1):
            item.setForeground(column, QColor(TEXT_COLOR))
            item.setBackground(column, QBrush(QColor(GROUP_DEFAULT)))

        item.setFont(0, QFont(FONT_FAMILY, FONT_SIZE + 1, QFont.Bold))

        if is_default:
            badge_font = QFont(FONT_FAMILY, max(FONT_SIZE - 1, 9), QFont.Bold)
            badge_font.setItalic(True)
            item.setText(1, "Default")
            item.setTextAlignment(1, Qt.AlignCenter)
            item.setFont(1, badge_font)
            item.setForeground(1, QColor(ACCENT_COLOR))
            item.setToolTip(0, 'Built-in default group for unassigned instances.')
            item.setToolTip(1, 'Built-in default group')

        tree.addTopLevelItem(item)
        return item

    def _proxy_display(self, inst):
        proxy = inst.get("proxy") or {}
        if not proxy.get("ip") or not proxy.get("port"):
            return {
                "indicator": "—",
                "indicator_color": QColor(TEXT_COLOR),
                "status_text": "Not applicable",
                "checked_at": "—",
                "reason": "",
            }

        proxy_test = inst.get("proxy_test")
        if isinstance(proxy_test, dict):
            ok = proxy_test.get("ok")
            checked_at = str(proxy_test.get("checked_at") or "").strip()
            reason = str(proxy_test.get("reason") or "").strip()
        else:
            ok = inst.get("proxy_ok")
            checked_at = ""
            reason = ""

        if ok is True:
            return {
                "indicator": "✓",
                "indicator_color": QColor("#62C766"),
                "status_text": "Passed",
                "checked_at": checked_at or "—",
                "reason": "",
            }

        if ok is False:
            return {
                "indicator": "✕",
                "indicator_color": QColor("#D04949"),
                "status_text": "Failed",
                "checked_at": checked_at or "—",
                "reason": reason or "Proxy test failed.",
            }

        return {
            "indicator": "…",
            "indicator_color": QColor(ACCENT_COLOR),
            "status_text": "Never tested",
            "checked_at": checked_at or "—",
            "reason": reason,
        }

    def refresh_tree(self, tree):
        self._tree = tree
        tree.clear()
        self.group_logic.load_groups()
        for group_name in self.group_logic.get_all_groups():
            group_item = self._make_group_item(tree, group_name)
            for inst in self.manager.data:
                if inst.get("group", "Unassigned") == group_name:
                    proxy_info = self._proxy_display(inst)
                    item = QTreeWidgetItem([" " + inst["name"], proxy_info["indicator"]])
                    item.setData(0, Qt.UserRole, {"type": "instance", "name": inst["name"]})
                    item.setTextAlignment(1, Qt.AlignCenter)
                    item.setForeground(1, proxy_info["indicator_color"])
                    for column in (0, 1):
                        item.setBackground(column, QBrush(QColor(INSTANCE_DEFAULT)))
                        if column == 0:
                            item.setForeground(column, QColor(TEXT_COLOR))
                    item.setFont(0, QFont(FONT_FAMILY, FONT_SIZE))
                    group_item.addChild(item)
            group_item.setExpanded(True)

    def _reselect(self, tree, name, item_type):
        if item_type == "group":
            for i in range(tree.topLevelItemCount()):
                group_item = tree.topLevelItem(i)
                info = group_item.data(0, Qt.UserRole) or {}
                if info.get("name") == name:
                    tree.setCurrentItem(group_item)
                    tree.scrollToItem(group_item)
                    return
        else:
            for i in range(tree.topLevelItemCount()):
                group_item = tree.topLevelItem(i)
                for j in range(group_item.childCount()):
                    child = group_item.child(j)
                    if (child.data(0, Qt.UserRole) or {}).get("name") == name:
                        tree.setCurrentItem(child)
                        tree.scrollToItem(child)
                        return

    def _item_by_name(self, name):
        if not self._tree:
            return None
        for i in range(self._tree.topLevelItemCount()):
            group_item = self._tree.topLevelItem(i)
            for j in range(group_item.childCount()):
                child = group_item.child(j)
                if (child.data(0, Qt.UserRole) or {}).get("name") == name:
                    return child
        return None

    def _on_proxy_tested(self, name, ok):
        item = self._item_by_name(name)
        inst = self.manager.get_instance(name)
        if item and inst:
            proxy_info = self._proxy_display(inst)
            item.setText(1, proxy_info["indicator"])
            item.setForeground(1, proxy_info["indicator_color"])

    def _current(self, tree):
        item = tree.currentItem()
        return item.data(0, Qt.UserRole) if item else None

    def _action_label(self, key):
        labels = {
            "create_instance": "Create Instance",
            "create_group": "Create Group",
            "launch": "Launch",
            "edit": "Edit",
            "delete": "Delete",
            "duplicate": "Duplicate",
            "move_up": "Move Up",
            "move_down": "Move Down",
        }
        return labels.get(key, key.replace("_", " ").title())

    def _available_actions_text(self, states, ordered_keys):
        labels = [self._action_label(key) for key in ordered_keys if states.get(key)]
        if not labels:
            return "No item-specific actions are available right now."
        return "Available now: " + ", ".join(labels)

    def get_action_states(self, tree):
        """Return which actions should be enabled for the current tree selection."""
        states = {
            "create_instance": True,
            "create_group": True,
            "launch": False,
            "edit": False,
            "delete": False,
            "duplicate": False,
            "move_up": False,
            "move_down": False,
        }

        current = tree.currentItem()
        if not current:
            return states

        info = current.data(0, Qt.UserRole) or {}
        item_type = info.get("type")
        name = info.get("name", "")

        if item_type == "group":
            index = tree.indexOfTopLevelItem(current)
            editable_group = not self._is_reserved_group(name)
            states["edit"] = editable_group
            states["delete"] = editable_group
            states["move_up"] = index > 0
            states["move_down"] = 0 <= index < tree.topLevelItemCount() - 1
        elif item_type == "instance":
            parent = current.parent()
            if parent:
                index = parent.indexOfChild(current)
                states["launch"] = True
                states["edit"] = True
                states["delete"] = True
                states["duplicate"] = True
                states["move_up"] = index > 0
                states["move_down"] = index < parent.childCount() - 1

        return states

    def get_selection_details(self, tree):
        """Return display-ready details for the current selection state."""
        groups = self.group_logic.get_all_groups()
        current = tree.currentItem()

        if not current:
            if not self.manager.data:
                return {
                    "badge_text": "Getting Started",
                    "badge_kind": "info",
                    "title": "No instances yet",
                    "message": "Create your first instance to start managing browser sessions. You can also create a group now and organise later.",
                    "rows": [
                        ("Groups", len(groups)),
                        ("Default Group", "Unassigned"),
                    ],
                    "actions_text": "Available now: Create Instance, Create Group",
                }

            return {
                "badge_text": "Selection",
                "badge_kind": "info",
                "title": "Nothing selected",
                "message": "Select a group or instance to see details here. You can also right-click tree items for quick actions.",
                "rows": [
                    ("Groups", len(groups)),
                    ("Instances", len(self.manager.data)),
                ],
                "actions_text": "Always available: Create Instance, Create Group",
            }

        info = current.data(0, Qt.UserRole) or {}
        states = self.get_action_states(tree)

        if info.get("type") == "group":
            group_name = info.get("name", "")
            instance_count = sum(1 for inst in self.manager.data if inst.get("group", "Unassigned") == group_name)
            position = tree.indexOfTopLevelItem(current) + 1
            is_default = self._is_reserved_group(group_name)

            return {
                "badge_text": "Default Group" if is_default else "Group",
                "badge_kind": "default" if is_default else "group",
                "title": group_name,
                "message": (
                    'This built-in group automatically holds instances that are not assigned to a custom group.'
                    if is_default
                    else "Use this custom group to keep related instances together."
                ),
                "rows": [
                    ("Instances", instance_count),
                    ("Position", f"{position} of {max(tree.topLevelItemCount(), 1)}"),
                    ("Type", "Built-in default group" if is_default else "Custom group"),
                ],
                "actions_text": self._available_actions_text(states, ("edit", "delete", "move_up", "move_down")),
            }

        if info.get("type") == "instance":
            name = info.get("name", "")
            inst = self.manager.get_instance(name) or {}
            proxy = inst.get("proxy") or {}
            group_name = inst.get("group", "Unassigned")
            landing_page = inst.get("landing_page") or "https://www.duckduckgo.com"
            proxy_info = self._proxy_display(inst)

            if proxy.get("ip") and proxy.get("port"):
                protocol = str(proxy.get("protocol", "proxy")).upper()
                auth_suffix = " (auth)" if proxy.get("auth") else ""
                proxy_text = f"{protocol} {proxy['ip']}:{proxy['port']}{auth_suffix}"
            else:
                proxy_text = "Not configured"

            rows = [
                ("Group", f"{group_name} (default)" if self._is_reserved_group(group_name) else group_name),
                ("Proxy", proxy_text),
                ("Proxy Status", proxy_info["status_text"]),
                ("Last Proxy Check", proxy_info["checked_at"]),
                ("Landing Page", landing_page),
            ]

            if proxy_info["reason"]:
                rows.insert(4, ("Proxy Note", proxy_info["reason"]))

            return {
                "badge_text": "Instance",
                "badge_kind": "instance",
                "title": name,
                "message": "Use the action strip or right-click this instance for quick actions.",
                "rows": rows,
                "actions_text": self._available_actions_text(
                    states,
                    ("launch", "edit", "duplicate", "delete", "move_up", "move_down"),
                ),
            }

        return {
            "badge_text": "Selection",
            "badge_kind": "info",
            "title": "Nothing selected",
            "message": "Select an item to see more details.",
            "rows": [],
            "actions_text": "Always available: Create Instance, Create Group",
        }

    def _format_launch_error(self, exc):
        message = str(exc).strip() or exc.__class__.__name__
        return message if len(message) <= 120 else f"{message[:117]}..."

    def _normalize_launch_result(self, result):
        """Support both the new structured launch result and older bool-style results."""
        if isinstance(result, dict):
            warnings_raw = result.get("warnings") or []
            if isinstance(warnings_raw, str):
                warnings_raw = [warnings_raw]

            warnings = []
            for warning in warnings_raw:
                text = str(warning).strip()
                if text and text not in warnings:
                    warnings.append(text)

            return {
                "started": bool(result.get("started")),
                "privacy_ok": bool(result.get("privacy_ok", not warnings)),
                "warnings": warnings,
            }

        if result is False:
            return {
                "started": False,
                "privacy_ok": False,
                "warnings": [],
            }

        return {
            "started": bool(result),
            "privacy_ok": True,
            "warnings": [],
        }

    def _format_launch_warning_summary(self, warnings):
        cleaned = []
        for warning in warnings:
            text = str(warning).strip()
            if text and text not in cleaned:
                cleaned.append(text)

        if not cleaned:
            return ""

        if len(cleaned) <= 3:
            return ", ".join(cleaned)

        return ", ".join(cleaned[:3]) + f", +{len(cleaned) - 3} more"

    def _handle_launch_result(self, name, future: Future):
        if future.cancelled():
            self.toastRequested.emit(f'Launch cancelled for "{name}".', "info")
            return

        try:
            result = future.result()
        except Exception as exc:
            self.toastRequested.emit(f'Launch failed for "{name}": {self._format_launch_error(exc)}', "error")
            return

        launch_result = self._normalize_launch_result(result)

        if not launch_result["started"]:
            self.toastRequested.emit(f'Launch failed for "{name}".', "error")
            return

        warning_summary = self._format_launch_warning_summary(launch_result["warnings"])
        if warning_summary or not launch_result["privacy_ok"]:
            if not warning_summary:
                warning_summary = "one or more privacy steps"

            # Use the existing info toast kind so this patch stays compatible
            # with the current toast system.
            self.toastRequested.emit(
                f'Browser started for "{name}" with privacy warnings: {warning_summary}.',
                "info",
            )
            return

        self.toastRequested.emit(f'Browser started for "{name}".', "success")

    def launch_selected(self, tree):
        d = self._current(tree)
        if d and d["type"] == "instance":
            future = self.manager.launch_instance(d["name"])
            if future is None:
                self.toastRequested.emit(f'Unable to launch "{d["name"]}".', "error")
                return
            self.toastRequested.emit(f'Starting browser for "{d["name"]}"...', "info")
            future.add_done_callback(lambda fut, name=d["name"]: self._handle_launch_result(name, fut))

    def edit_selected(self, tree, parent):
        d = self._current(tree)
        if not d:
            return

        if d["type"] == "group":
            if self._is_reserved_group(d["name"]):
                self.toastRequested.emit(
                    'The "Unassigned" group is built in and cannot be edited.',
                    "info",
                )
                return
            dlg = GuiGroupManager(parent, group_name=d["name"])
        else:
            dlg = GuiInstanceManager(self.manager, d["name"], parent)

        dlg.accepted.connect(lambda: self.refresh_tree(tree))
        dlg.exec()

    def _sync_deleted_group_instances(self, group_name):
        for inst in self.manager.data:
            if inst.get("group", "Unassigned").casefold() == group_name.casefold():
                inst["group"] = "Unassigned"

    def delete_selected(self, tree):
        d = self._current(tree)
        if not d:
            return

        if d["type"] == "group":
            if self._is_reserved_group(d["name"]):
                self.toastRequested.emit(
                    'The "Unassigned" group is built in and cannot be deleted.',
                    "info",
                )
                return

            answer = QMessageBox.question(
                tree,
                "Delete Group",
                f'Delete the group "{d["name"]}"?\n\nAny instances in this group will be moved to "Unassigned".',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

            self.group_logic.delete_group(d["name"])
            self._sync_deleted_group_instances(d["name"])
            self.refresh_tree(tree)
            self.toastRequested.emit(f'Group "{d["name"]}" deleted.', "success")
            return

        answer = QMessageBox.question(
            tree,
            "Delete Instance",
            f'Delete the instance "{d["name"]}"?\n\nThis cannot be undone.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        self.manager.delete_instance(d["name"])
        self.refresh_tree(tree)
        self.toastRequested.emit(f'Instance "{d["name"]}" deleted.', "success")

    def duplicate_selected(self, tree):
        d = self._current(tree)
        if d and d["type"] == "instance":
            self.manager.duplicate_instance(d["name"])
            self.refresh_tree(tree)
            self.toastRequested.emit(f'Instance "{d["name"]}" duplicated.', "success")

    def create_new_instance(self, parent):
        dlg = GuiInstanceManager(self.manager, None, parent)
        dlg.accepted.connect(lambda: parent.logic.refresh_tree(parent.tree))
        dlg.exec()

    def create_new_group(self, parent):
        dlg = GuiGroupManager(parent, group_name=None)
        dlg.accepted.connect(lambda: parent.logic.refresh_tree(parent.tree))
        dlg.exec()

    def move_selected_up(self, tree):
        current = tree.currentItem()
        if not current:
            return
        info = current.data(0, Qt.UserRole) or {}
        selected_name = info.get("name")
        if info.get("type") == "group":
            groups = self.group_logic.get_all_groups()
            index = groups.index(selected_name)
            if index <= 0:
                return
            groups[index - 1], groups[index] = groups[index], groups[index - 1]
            self.group_logic.reorder_groups(groups)
        else:
            parent = current.parent()
            if not parent:
                return
            names = [parent.child(i).data(0, Qt.UserRole)["name"] for i in range(parent.childCount())]
            index = names.index(selected_name)
            if index <= 0:
                return
            names[index - 1], names[index] = names[index], names[index - 1]
            self.manager.rearrange_group_instances((parent.data(0, Qt.UserRole) or {}).get("name", parent.text(0)), names)
        self.refresh_tree(tree)
        self._reselect(tree, selected_name, info.get("type"))

    def move_selected_down(self, tree):
        current = tree.currentItem()
        if not current:
            return
        info = current.data(0, Qt.UserRole) or {}
        selected_name = info.get("name")
        if info.get("type") == "group":
            groups = self.group_logic.get_all_groups()
            index = groups.index(selected_name)
            if index >= len(groups) - 1:
                return
            groups[index], groups[index + 1] = groups[index + 1], groups[index]
            self.group_logic.reorder_groups(groups)
        else:
            parent = current.parent()
            if not parent:
                return
            names = [parent.child(i).data(0, Qt.UserRole)["name"] for i in range(parent.childCount())]
            index = names.index(selected_name)
            if index >= len(names) - 1:
                return
            names[index], names[index + 1] = names[index + 1], names[index]
            self.manager.rearrange_group_instances((parent.data(0, Qt.UserRole) or {}).get("name", parent.text(0)), names)
        self.refresh_tree(tree)
        self._reselect(tree, selected_name, info.get("type"))

    def open_commands(self):
        webbrowser.open("https://www.jivaro.net/downloads/programs/info/instanciar")

    def open_about_jivaro(self):
        webbrowser.open("https://www.jivaro.net/")

    def open_discord(self):
        webbrowser.open("https://discord.gg/GDfX5BFGye")

    def open_proxies(self):
        webbrowser.open("https://jivaro.net/content/blog/the-best-affordable-proxy-providers")