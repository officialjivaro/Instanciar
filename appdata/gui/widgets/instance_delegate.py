# appdata/gui/widgets/instance_delegate.py
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QBrush, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QStyledItemDelegate

from appdata.config.style_constants import (
    BUTTON_TEXT_LIGHT,
    PROXY_DEFAULT_COLOR,
    PROXY_FAIL_COLOR,
    PROXY_OK_COLOR,
)


class InstanceDelegate(QStyledItemDelegate):
    """Paint small status chips for instance rows."""

    def paint(self, painter: QPainter, option, index):
        super().paint(painter, option, index)
        data = index.data(Qt.UserRole) or {}
        if data.get("type") != "instance":
            return

        chip = str(data.get("status", "OK"))
        chip_color = self._chip_color(chip)

        metrics = QFontMetrics(option.font)
        width = metrics.horizontalAdvance(chip) + 16
        height = 18
        rect = QRectF(option.rect.right() - width - 8, option.rect.center().y() - height / 2, width, height)

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(chip_color)))
        painter.setPen(QPen(Qt.NoPen))
        painter.drawRoundedRect(rect, 9, 9)
        painter.setPen(QPen(QColor(BUTTON_TEXT_LIGHT)))
        painter.drawText(rect, Qt.AlignCenter, chip)
        painter.restore()

    @staticmethod
    def _chip_color(chip: str) -> str:
        normalized = chip.strip().lower()
        if normalized in {"ok", "✓", "default"}:
            return PROXY_OK_COLOR if normalized != "default" else PROXY_DEFAULT_COLOR
        if normalized in {"x", "✕", "✖", "failed", "error"}:
            return PROXY_FAIL_COLOR
        return PROXY_DEFAULT_COLOR
