# appdata/gui/widgets/instance_delegate.py
from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QFontMetrics
from PySide6.QtCore import QRectF, Qt
from appdata.config.style_constants import ACCENT_COLOR, TEXT_COLOR

class InstanceDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option, index):
        super().paint(painter, option, index)
        d = index.data(Qt.UserRole) or {}
        if d.get("type") != "instance":
            return
        chip = d.get("status", "OK")
        metrics = QFontMetrics(option.font)
        w = metrics.horizontalAdvance(chip) + 16
        h = 18
        rect = QRectF(option.rect.right() - w - 8, option.rect.center().y() - h / 2, w, h)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(ACCENT_COLOR)))
        painter.setPen(QPen(Qt.NoPen))
        painter.drawRoundedRect(rect, 9, 9)
        painter.setPen(QPen(QColor(TEXT_COLOR)))
        painter.drawText(rect, Qt.AlignCenter, chip)
