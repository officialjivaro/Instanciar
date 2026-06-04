# appdata/gui/themes/app_theme.py
"""
Shared Instanciar UI theme helpers.

The dashboard uses one dark visual system so widgets do not need large local
style strings. Widget roles are set through dynamic properties.
"""

from typing import Optional

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QWidget

from appdata.config.style_constants import (
    ACCENT_COLOR,
    ACCENT_COLOR_HOVER,
    APP_BACKGROUND,
    BORDER_COLOR,
    BORDER_COLOR_STRONG,
    BUTTON_TEXT_LIGHT,
    CARD_BACKGROUND,
    CARD_BACKGROUND_LIGHT,
    DANGER_COLOR,
    DANGER_COLOR_HOVER,
    FOCUS_COLOR,
    FONT_FAMILY,
    FONT_SIZE,
    GROUP_HOVER,
    INSTANCE_DEFAULT,
    MUTED_TEXT_COLOR,
    PALETTE_CHARCOAL,
    SIDEBAR_BACKGROUND,
    SUBTLE_TEXT_COLOR,
    SUCCESS_COLOR,
    SURFACE_COLOR,
    SURFACE_SOFT,
    TEXT_COLOR,
    WARNING_COLOR,
    WARNING_COLOR_HOVER,
)


APP_STYLESHEET = f"""
QMainWindow,
QDialog {{
    background-color: {APP_BACKGROUND};
    color: {TEXT_COLOR};
    font-family: "{FONT_FAMILY}";
    font-size: {FONT_SIZE}pt;
}}

QWidget#MainCentralWidget,
QWidget#DialogRoot {{
    background-color: {APP_BACKGROUND};
    color: {TEXT_COLOR};
}}

QLabel {{
    color: {TEXT_COLOR};
    background: transparent;
}}

QLabel:disabled {{
    color: {SUBTLE_TEXT_COLOR};
}}

QLabel[role="eyebrow"] {{
    color: {WARNING_COLOR};
    font-weight: 800;
    letter-spacing: 0.4px;
    text-transform: uppercase;
}}

QLabel[role="appTitle"] {{
    color: {TEXT_COLOR};
    font-size: {FONT_SIZE + 9}pt;
    font-weight: 900;
}}

QLabel[role="appSubtitle"] {{
    color: {MUTED_TEXT_COLOR};
    font-size: {FONT_SIZE + 1}pt;
}}

QLabel[role="sectionTitle"] {{
    color: {TEXT_COLOR};
    font-weight: 850;
}}

QLabel[role="compactSectionTitle"] {{
    color: {TEXT_COLOR};
    font-size: {max(FONT_SIZE - 1, 9)}pt;
    font-weight: 850;
}}

QLabel[role="sectionHint"] {{
    color: {SUBTLE_TEXT_COLOR};
}}

QLabel[role="statNumber"] {{
    color: {TEXT_COLOR};
    font-size: {FONT_SIZE + 8}pt;
    font-weight: 900;
}}

QLabel[role="statLabel"] {{
    color: {SUBTLE_TEXT_COLOR};
    font-size: {FONT_SIZE - 1}pt;
    font-weight: 700;
}}

QLabel[role="detailKey"] {{
    color: {SUBTLE_TEXT_COLOR};
    font-size: {FONT_SIZE - 1}pt;
    font-weight: 800;
}}

QLabel[role="detailValue"] {{
    color: {MUTED_TEXT_COLOR};
}}

QLabel[role="detailValue"][state="warning"] {{
    color: {WARNING_COLOR};
    font-weight: 800;
}}

QLabel[role="emptyState"] {{
    color: {SUBTLE_TEXT_COLOR};
    font-size: {FONT_SIZE + 1}pt;
}}

QLabel#DetailsTitle {{
    color: {TEXT_COLOR};
    font-size: {FONT_SIZE + 6}pt;
    font-weight: 900;
}}

QLabel#SelectionBadge {{
    border-radius: 12px;
    padding: 5px 11px;
    color: {BUTTON_TEXT_LIGHT};
    font-weight: 900;
}}

QLabel#SelectionBadge[state="info"],
QLabel#SelectionBadge[state="group"],
QLabel#SelectionBadge[state="default"] {{
    background-color: {ACCENT_COLOR};
}}

QLabel#SelectionBadge[state="instance"] {{
    background-color: {WARNING_COLOR};
}}

QLabel#SelectionBadge[state="success"] {{
    background-color: {SUCCESS_COLOR};
}}

QLabel#SelectionBadge[state="error"] {{
    background-color: {DANGER_COLOR};
}}

QMenuBar {{
    background-color: {APP_BACKGROUND};
    color: {TEXT_COLOR};
    border-bottom: 1px solid {BORDER_COLOR};
    padding: 5px 8px;
}}

QMenuBar::item {{
    background: transparent;
    padding: 7px 12px;
    border-radius: 8px;
}}

QMenuBar::item:selected {{
    background-color: {GROUP_HOVER};
}}

QMenu {{
    background-color: {CARD_BACKGROUND};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 10px;
    padding: 6px;
}}

QMenu::item {{
    padding: 7px 18px;
    border-radius: 8px;
}}

QMenu::item:selected {{
    background-color: {GROUP_HOVER};
}}

QMenu::item:disabled {{
    color: {SUBTLE_TEXT_COLOR};
}}

QFrame#DashboardSidebar {{
    background-color: {SIDEBAR_BACKGROUND};
    border: 1px solid {BORDER_COLOR};
    border-radius: 20px;
}}

QFrame#SidebarBrandCard,
QFrame#SidebarStatCard,
QFrame#SidebarSupportCard,
QFrame#WorkspaceTopCard,
QFrame#TreeWorkspaceCard,
QFrame#DashboardFilterBar,
QFrame#selectionDetailsPanel,
QFrame#CommandBarCard,
QFrame#DetailCard,
QFrame#DetailRow {{
    background-color: {CARD_BACKGROUND};
    border: 1px solid {BORDER_COLOR};
    border-radius: 12px;
}}

QFrame#SidebarBrandCard {{
    border-top: 3px solid {ACCENT_COLOR};
}}

QFrame#WorkspaceTopCard {{
    border-top: 3px solid {WARNING_COLOR};
}}

QFrame#TreeWorkspaceCard {{
    border-radius: 18px;
}}

QFrame#CommandBarCard {{
    background-color: transparent;
    border: none;
}}

QFrame#CommandSection {{
    background-color: {SURFACE_SOFT};
    border: 1px solid {BORDER_COLOR};
    border-radius: 12px;
}}

QFrame#CommandSection QPushButton {{
    min-height: 28px;
    padding: 5px 9px;
    border-radius: 10px;
}}

QFrame#DashboardFilterBar {{
    background-color: {SURFACE_SOFT};
}}

QFrame#DetailsRowsHost {{
    background: transparent;
    border: none;
}}

QFrame#ActionDivider {{
    background-color: {BORDER_COLOR};
    max-height: 1px;
    min-height: 1px;
    border: none;
}}

QGroupBox {{
    background-color: {CARD_BACKGROUND};
    border: 1px solid {BORDER_COLOR};
    border-radius: 14px;
    margin-top: 14px;
    padding-top: 10px;
    color: {TEXT_COLOR};
    font-weight: 800;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    color: {TEXT_COLOR};
}}

QLineEdit,
QComboBox,
QPlainTextEdit,
QTextEdit,
QSpinBox,
QDoubleSpinBox {{
    background-color: {INSTANCE_DEFAULT};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 11px;
    padding: 8px 11px;
    selection-background-color: {ACCENT_COLOR};
    selection-color: {BUTTON_TEXT_LIGHT};
}}

QLineEdit:hover,
QComboBox:hover,
QPlainTextEdit:hover,
QTextEdit:hover,
QSpinBox:hover,
QDoubleSpinBox:hover {{
    border-color: {BORDER_COLOR_STRONG};
}}

QLineEdit:focus,
QComboBox:focus,
QPlainTextEdit:focus,
QTextEdit:focus,
QSpinBox:focus,
QDoubleSpinBox:focus {{
    border: 1px solid {FOCUS_COLOR};
}}

QLineEdit:disabled,
QComboBox:disabled,
QPlainTextEdit:disabled,
QTextEdit:disabled {{
    background-color: #141C19;
    color: {SUBTLE_TEXT_COLOR};
    border-color: #25342E;
}}

QComboBox::drop-down {{
    width: 26px;
    border: none;
    border-left: 1px solid {BORDER_COLOR};
    background-color: {SURFACE_COLOR};
    border-top-right-radius: 11px;
    border-bottom-right-radius: 11px;
}}

QComboBox QAbstractItemView {{
    background-color: {CARD_BACKGROUND};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    selection-background-color: {ACCENT_COLOR};
    selection-color: {BUTTON_TEXT_LIGHT};
}}

QPushButton {{
    min-height: 30px;
    background-color: {SURFACE_COLOR};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 10px;
    padding: 5px 9px;
    font-weight: 800;
}}

QPushButton:hover {{
    background-color: {GROUP_HOVER};
    border-color: {BORDER_COLOR_STRONG};
}}

QPushButton:pressed {{
    background-color: #19231F;
    border-color: {FOCUS_COLOR};
}}

QPushButton:focus {{
    border-color: {FOCUS_COLOR};
}}

QPushButton:disabled {{
    background-color: #171F1C;
    color: #718279;
    border-color: #25342E;
}}

QPushButton[role="primary"] {{
    background-color: {ACCENT_COLOR};
    border-color: #719783;
    color: {BUTTON_TEXT_LIGHT};
}}

QPushButton[role="primary"]:hover {{
    background-color: {ACCENT_COLOR_HOVER};
    border-color: #95B7A4;
}}

QPushButton[role="accent"] {{
    background-color: {WARNING_COLOR};
    border-color: #F0A36A;
    color: {BUTTON_TEXT_LIGHT};
}}

QPushButton[role="accent"]:hover {{
    background-color: {WARNING_COLOR_HOVER};
    border-color: #FFC095;
}}

QPushButton[role="secondary"] {{
    background-color: {CARD_BACKGROUND_LIGHT};
    border-color: {BORDER_COLOR};
}}

QPushButton[role="muted"] {{
    background-color: #18211D;
    color: {MUTED_TEXT_COLOR};
}}

QPushButton[role="danger"] {{
    background-color: #3A221F;
    border-color: {DANGER_COLOR};
    color: #FFE4DE;
}}

QPushButton[role="danger"]:hover {{
    background-color: #4A2925;
    border-color: {DANGER_COLOR_HOVER};
}}

QPushButton[role="donate"] {{
    min-height: 34px;
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 {WARNING_COLOR},
        stop: 1 #F29B5D
    );
    border-color: #FFC097;
    color: {BUTTON_TEXT_LIGHT};
}}

QPushButton[role="donate"]:hover {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #EA8B4E,
        stop: 1 #FFB172
    );
}}

QPushButton[role="sidebarAction"] {{
    text-align: left;
    padding-left: 14px;
}}

QCheckBox,
QRadioButton {{
    color: {MUTED_TEXT_COLOR};
    spacing: 8px;
}}

QCheckBox:disabled,
QRadioButton:disabled {{
    color: {SUBTLE_TEXT_COLOR};
}}

QCheckBox::indicator,
QRadioButton::indicator {{
    width: 17px;
    height: 17px;
    border: 1px solid {BORDER_COLOR};
    background-color: {INSTANCE_DEFAULT};
}}

QCheckBox::indicator {{
    border-radius: 5px;
}}

QRadioButton::indicator {{
    border-radius: 9px;
}}

QCheckBox::indicator:hover,
QRadioButton::indicator:hover {{
    border-color: {FOCUS_COLOR};
}}

QCheckBox::indicator:checked,
QRadioButton::indicator:checked {{
    background-color: {ACCENT_COLOR};
    border-color: {FOCUS_COLOR};
}}

QTreeWidget {{
    background-color: {INSTANCE_DEFAULT};
    alternate-background-color: #151D19;
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 14px;
    padding: 4px;
    outline: none;
}}

QTreeWidget::item {{
    min-height: 30px;
    padding: 5px 8px;
    border-radius: 8px;
}}

QTreeWidget::item:hover {{
    background-color: {GROUP_HOVER};
}}

QTreeWidget::item:selected {{
    background-color: #587C67;
    color: {BUTTON_TEXT_LIGHT};
    border: 1px solid #9ABAA7;
}}

QHeaderView::section {{
    background-color: {CARD_BACKGROUND_LIGHT};
    color: {TEXT_COLOR};
    border: none;
    border-right: 1px solid {BORDER_COLOR};
    border-bottom: 1px solid {BORDER_COLOR};
    padding: 8px 10px;
    font-weight: 900;
}}

QSplitter::handle {{
    background-color: {BORDER_COLOR};
    border-radius: 2px;
}}

QScrollArea {{
    background: transparent;
    border: none;
}}

QScrollBar:vertical,
QScrollBar:horizontal {{
    background: transparent;
    border: none;
    margin: 2px;
}}

QScrollBar::handle:vertical,
QScrollBar::handle:horizontal {{
    background: {SURFACE_COLOR};
    border-radius: 6px;
    min-height: 28px;
    min-width: 28px;
}}

QScrollBar::handle:vertical:hover,
QScrollBar::handle:horizontal:hover {{
    background: {ACCENT_COLOR};
}}

QScrollBar::add-line,
QScrollBar::sub-line,
QScrollBar::add-page,
QScrollBar::sub-page {{
    background: transparent;
    border: none;
}}

QProgressBar {{
    background-color: {INSTANCE_DEFAULT};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    border-radius: 7px;
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 {ACCENT_COLOR},
        stop: 1 {WARNING_COLOR}
    );
}}

QLabel#InstallProgressVisual {{
    background-color: {INSTANCE_DEFAULT};
    border: 1px solid {BORDER_COLOR};
    border-radius: 14px;
    color: {TEXT_COLOR};
    font-size: {FONT_SIZE + 2}pt;
    font-weight: 900;
}}

QTabWidget::pane {{
    background-color: {CARD_BACKGROUND};
    border: 1px solid {BORDER_COLOR};
    border-radius: 12px;
    top: -1px;
}}

QTabBar::tab {{
    background-color: {SURFACE_COLOR};
    color: {MUTED_TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-bottom: none;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    padding: 8px 14px;
    margin-right: 4px;
    font-weight: 800;
}}

QTabBar::tab:selected {{
    background-color: {CARD_BACKGROUND};
    color: {TEXT_COLOR};
    border-color: {BORDER_COLOR_STRONG};
}}

QTabBar::tab:hover {{
    color: {TEXT_COLOR};
    border-color: {ACCENT_COLOR};
}}

QDialog#WhatsNewDialogRoot {{
    background-color: {APP_BACKGROUND};
    color: {TEXT_COLOR};
}}

QFrame#WhatsNewHeader {{
    background-color: {CARD_BACKGROUND};
    border: 1px solid {BORDER_COLOR};
    border-top: 3px solid {WARNING_COLOR};
    border-radius: 16px;
}}

QTextBrowser#WhatsNewViewer {{
    background-color: {INSTANCE_DEFAULT};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 14px;
    padding: 12px;
    selection-background-color: {ACCENT_COLOR};
    selection-color: {BUTTON_TEXT_LIGHT};
}}

QTextBrowser#WhatsNewViewer a {{
    color: {WARNING_COLOR};
}}

"""


def _set_palette(app: QApplication) -> None:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(APP_BACKGROUND))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_COLOR))
    palette.setColor(QPalette.ColorRole.Base, QColor(INSTANCE_DEFAULT))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(CARD_BACKGROUND))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(CARD_BACKGROUND))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(TEXT_COLOR))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT_COLOR))
    palette.setColor(QPalette.ColorRole.Button, QColor(SURFACE_COLOR))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT_COLOR))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT_COLOR))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(BUTTON_TEXT_LIGHT))
    app.setPalette(palette)


def _repolish(widget: Optional[QWidget]) -> None:
    if widget is None:
        return
    style = widget.style()
    if style is None:
        return
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def apply_app_theme(widget: Optional[QWidget] = None) -> None:
    app = QApplication.instance()
    if app is None:
        return
    _set_palette(app)
    if app.styleSheet() != APP_STYLESHEET:
        app.setStyleSheet(APP_STYLESHEET)
    _repolish(widget)


def set_widget_role(widget: Optional[QWidget], role: str) -> None:
    if widget is None:
        return
    if widget.property("role") == role:
        return
    widget.setProperty("role", role)
    _repolish(widget)


def set_widget_state(widget: Optional[QWidget], state: str) -> None:
    if widget is None:
        return
    if widget.property("state") == state:
        return
    widget.setProperty("state", state)
    _repolish(widget)
