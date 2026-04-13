# appdata/gui/widgets/instance_tree.py
from PySide6.QtWidgets import QTreeWidget, QAbstractItemView
from PySide6.QtCore import Qt


class InstanceTree(QTreeWidget):
    """Tree widget used for group / instance browsing and drag-drop reordering."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Groups & Instances", "Proxy Status"])
        self.setIndentation(18)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragDropMode(QAbstractItemView.InternalMove)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.viewport().width()
        primary = int(width * 0.80)
        self.setColumnWidth(0, primary)
        self.setColumnWidth(1, width - primary)

    def mimeData(self, items):
        mime = super().mimeData(items)
        info = items[0].data(0, Qt.UserRole) or {}
        if info.get("type") == "instance":
            mime.setText(info["name"])
        return mime

    def _is_group(self, item):
        return (item.data(0, Qt.UserRole) or {}).get("type") == "group"

    def _is_instance(self, item):
        return (item.data(0, Qt.UserRole) or {}).get("type") == "instance"

    def _group_name(self, item):
        info = item.data(0, Qt.UserRole) or {}
        return info.get("name", item.text(0))

    def dragMoveEvent(self, event):
        target = self.itemAt(event.pos())
        position = self.dropIndicatorPosition()
        accept = False

        if target:
            if position == QAbstractItemView.OnItem and self._is_group(target):
                accept = True
                self.setCurrentItem(target)
            elif position in (QAbstractItemView.AboveItem, QAbstractItemView.BelowItem) and self._is_instance(target):
                accept = True
        else:
            if position == QAbstractItemView.OnViewport:
                accept = True

        event.acceptProposedAction() if accept else event.ignore()

    def dropEvent(self, event):
        target = self.itemAt(event.pos())
        position = self.dropIndicatorPosition()

        if target and position == QAbstractItemView.OnItem and self._is_group(target):
            main_window = self.window()
            if hasattr(main_window, "logic"):
                main_window.logic.manager.save_instance_group(event.mimeData().text(), self._group_name(target))
                main_window.logic.refresh_tree(self)
                if hasattr(main_window, "_refresh_selection_ui"):
                    main_window._refresh_selection_ui()
            return

        super().dropEvent(event)

        per_group = {}
        for group_index in range(self.topLevelItemCount()):
            group_item = self.topLevelItem(group_index)
            group_name = self._group_name(group_item)
            per_group[group_name] = [
                group_item.child(child_index).data(0, Qt.UserRole)["name"]
                for child_index in range(group_item.childCount())
            ]

        main_window = self.window()
        if hasattr(main_window, "logic"):
            for group_name, order in per_group.items():
                main_window.logic.manager.rearrange_group_instances(group_name, order)
            if hasattr(main_window, "_refresh_selection_ui"):
                main_window._refresh_selection_ui()