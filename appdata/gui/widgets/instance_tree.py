# appdata/gui/widgets/instance_tree.py
from PySide6.QtWidgets import QTreeWidget, QAbstractItemView
from PySide6.QtCore import Qt, QMimeData


class InstanceTree(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Groups & Instances", "Proxy Status"])
        self.setIndentation(18)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragDropMode(QAbstractItemView.InternalMove)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        w = self.viewport().width()
        self.setColumnWidth(0, int(w * 0.80))
        self.setColumnWidth(1, w - int(w * 0.80))

    def mimeData(self, items):
        md = super().mimeData(items)
        info = items[0].data(0, Qt.UserRole) or {}
        if info.get("type") == "instance":
            md.setText(info["name"])
        return md

    def _is_group(self, item):
        return (item.data(0, Qt.UserRole) or {}).get("type") == "group"

    def _is_instance(self, item):
        return (item.data(0, Qt.UserRole) or {}).get("type") == "instance"

    def dragMoveEvent(self, e):
        tgt = self.itemAt(e.pos())
        pos = self.dropIndicatorPosition()
        accept = False
        if tgt:
            if pos == QAbstractItemView.OnItem and self._is_group(tgt):
                accept = True
                self.setCurrentItem(tgt)
            elif pos in (QAbstractItemView.AboveItem, QAbstractItemView.BelowItem) and self._is_instance(tgt):
                accept = True
        else:
            if pos == QAbstractItemView.OnViewport:
                accept = True
        e.acceptProposedAction() if accept else e.ignore()

    def dropEvent(self, e):
        tgt = self.itemAt(e.pos())
        pos = self.dropIndicatorPosition()
        if tgt and pos == QAbstractItemView.OnItem and self._is_group(tgt):
            mw = self.window()
            if hasattr(mw, "logic"):
                mw.logic.manager.save_instance_group(e.mimeData().text(), tgt.text(0))
                mw.logic.refresh_tree(self)
            return
        super().dropEvent(e)
        per_group = {}
        for gi in range(self.topLevelItemCount()):
            g_item = self.topLevelItem(gi)
            g_name = g_item.text(0)
            per_group[g_name] = [
                g_item.child(ci).data(0, Qt.UserRole)["name"]
                for ci in range(g_item.childCount())
            ]
        mw = self.window()
        if hasattr(mw, "logic"):
            for g, order in per_group.items():
                mw.logic.manager.rearrange_group_instances(g, order)
