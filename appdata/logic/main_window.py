# appdata/logic/main_window.py
import threading, webbrowser
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont, QColor, QBrush
from PySide6.QtWidgets import QTreeWidgetItem
from appdata.gui.instance_manager import GuiInstanceManager
from appdata.gui.group_manager import GuiGroupManager
from appdata.logic.group_manager import GroupManagerLogic
from appdata.config.style_constants import GROUP_DEFAULT, INSTANCE_DEFAULT, TEXT_COLOR, FONT_FAMILY, FONT_SIZE


class MainWindowLogic(QObject):
    toastRequested = Signal(str)

    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.group_logic = GroupManagerLogic()
        self.manager.proxyTested.connect(self._on_proxy_tested)
        self._tree = None

    def _make_group_item(self, tree, name):
        it = QTreeWidgetItem([name, ""])
        it.setData(0, Qt.UserRole, {"type": "group", "name": name})
        for c in (0, 1):
            it.setForeground(c, QColor(TEXT_COLOR))
            it.setBackground(c, QBrush(QColor(GROUP_DEFAULT)))
        it.setFont(0, QFont(FONT_FAMILY, FONT_SIZE + 1, QFont.Bold))
        tree.addTopLevelItem(it)
        return it

    def refresh_tree(self, tree):
        self._tree = tree
        tree.clear()
        self.group_logic.load_groups()
        for g in self.group_logic.get_all_groups():
            gitem = self._make_group_item(tree, g)
            for inst in self.manager.data:
                if inst.get("group", "Unassigned") == g:
                    ok = inst.get("proxy_ok", True)
                    it = QTreeWidgetItem([" " + inst["name"], "✓" if ok else "✕"])
                    it.setData(0, Qt.UserRole, {"type": "instance", "name": inst["name"]})
                    it.setTextAlignment(1, Qt.AlignCenter)
                    it.setForeground(1, QColor("#62c766") if ok else QColor("#d04949"))
                    for c in (0, 1):
                        it.setBackground(c, QBrush(QColor(INSTANCE_DEFAULT)))
                        if c == 0:
                            it.setForeground(c, QColor(TEXT_COLOR))
                    it.setFont(0, QFont(FONT_FAMILY, FONT_SIZE))
                    gitem.addChild(it)
            gitem.setExpanded(True)

    def _reselect(self, tree, name, type_):
        if type_ == "group":
            for i in range(tree.topLevelItemCount()):
                g = tree.topLevelItem(i)
                if g.text(0) == name:
                    tree.setCurrentItem(g)
                    tree.scrollToItem(g)
                    return
        else:
            for i in range(tree.topLevelItemCount()):
                g = tree.topLevelItem(i)
                for j in range(g.childCount()):
                    c = g.child(j)
                    if (c.data(0, Qt.UserRole) or {}).get("name") == name:
                        tree.setCurrentItem(c)
                        tree.scrollToItem(c)
                        return

    def _item_by_name(self, name):
        if not self._tree:
            return None
        for i in range(self._tree.topLevelItemCount()):
            g = self._tree.topLevelItem(i)
            for j in range(g.childCount()):
                c = g.child(j)
                if (c.data(0, Qt.UserRole) or {}).get("name") == name:
                    return c
        return None

    def _on_proxy_tested(self, name, ok):
        it = self._item_by_name(name)
        if it:
            it.setText(1, "✓" if ok else "✕")
            it.setForeground(1, QColor("#62c766") if ok else QColor("#d04949"))

    def _current(self, tree):
        it = tree.currentItem()
        return it.data(0, Qt.UserRole) if it else None

    def launch_selected(self, tree):
        d = self._current(tree)
        if d and d["type"] == "instance":
            threading.Thread(target=self.manager.launch_instance, args=(d["name"],), daemon=True).start()
            self.toastRequested.emit(f"Launching {d['name']}")

    def edit_selected(self, tree, parent):
        d = self._current(tree)
        if not d:
            return
        dlg = GuiGroupManager(parent, group_name=d["name"]) if d["type"] == "group" else GuiInstanceManager(
            self.manager, d["name"], parent
        )
        dlg.accepted.connect(lambda: self.refresh_tree(tree))
        dlg.exec()

    def delete_selected(self, tree):
        d = self._current(tree)
        if not d:
            return
        if d["type"] == "group":
            self.group_logic.delete_group(d["name"])
        else:
            self.manager.delete_instance(d["name"])
        self.refresh_tree(tree)
        self.toastRequested.emit("Deleted")

    def duplicate_selected(self, tree):
        d = self._current(tree)
        if d and d["type"] == "instance":
            self.manager.duplicate_instance(d["name"])
            self.refresh_tree(tree)
            self.toastRequested.emit("Duplicated")

    def create_new_instance(self, parent):
        dlg = GuiInstanceManager(self.manager, None, parent)
        dlg.accepted.connect(lambda: parent.logic.refresh_tree(parent.tree))
        dlg.exec()

    def create_new_group(self, parent):
        dlg = GuiGroupManager(parent, group_name=None)
        dlg.accepted.connect(lambda: parent.logic.refresh_tree(parent.tree))
        dlg.exec()

    def move_selected_up(self, tree):
        cur = tree.currentItem()
        if not cur:
            return
        info = cur.data(0, Qt.UserRole) or {}
        sel_name = info.get("name")
        if info.get("type") == "group":
            groups = self.group_logic.get_all_groups()
            idx = groups.index(sel_name)
            if idx <= 0:
                return
            groups[idx - 1], groups[idx] = groups[idx], groups[idx - 1]
            self.group_logic.reorder_groups(groups)
        else:
            parent = cur.parent()
            if not parent:
                return
            names = [parent.child(i).data(0, Qt.UserRole)["name"] for i in range(parent.childCount())]
            idx = names.index(sel_name)
            if idx <= 0:
                return
            names[idx - 1], names[idx] = names[idx], names[idx - 1]
            self.manager.rearrange_group_instances(parent.text(0), names)
        self.refresh_tree(tree)
        self._reselect(tree, sel_name, info.get("type"))

    def move_selected_down(self, tree):
        cur = tree.currentItem()
        if not cur:
            return
        info = cur.data(0, Qt.UserRole) or {}
        sel_name = info.get("name")
        if info.get("type") == "group":
            groups = self.group_logic.get_all_groups()
            idx = groups.index(sel_name)
            if idx >= len(groups) - 1:
                return
            groups[idx], groups[idx + 1] = groups[idx + 1], groups[idx]
            self.group_logic.reorder_groups(groups)
        else:
            parent = cur.parent()
            if not parent:
                return
            names = [parent.child(i).data(0, Qt.UserRole)["name"] for i in range(parent.childCount())]
            idx = names.index(sel_name)
            if idx >= len(names) - 1:
                return
            names[idx], names[idx + 1] = names[idx + 1], names[idx]
            self.manager.rearrange_group_instances(parent.text(0), names)
        self.refresh_tree(tree)
        self._reselect(tree, sel_name, info.get("type"))

    def open_commands(self):
        webbrowser.open("https://www.jivaro.net/downloads/programs/info/instanciar")

    def open_about_jivaro(self):
        webbrowser.open("https://www.jivaro.net/")

    def open_discord(self):
        webbrowser.open("https://discord.gg/GDfX5BFGye")

    def open_proxies(self):
        webbrowser.open("https://jivaro.net/content/blog/the-best-affordable-proxy-providers")
