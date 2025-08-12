from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDialog, QLayout, QWidget, QVBoxLayout, QLabel, QApplication
from app.config import settings as app_settings


PRIMARY_COLOR = "#007065"


def apply_dialog_theme(dialog: QDialog, min_width: int = 520, content_margins: tuple[int, int, int, int] = (14, 12, 14, 12), spacing: int = 10) -> None:
    """Aplica um tema consistente a diálogos.

    - Remove botão de ajuda do título
    - Define largura mínima padrão
    - Margens e espaçamento uniformes
    - Estiliza inputs e botões (cor principal PRIMARY_COLOR)
    """
    # Flags de janela
    dialog.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
    dialog.setModal(True)
    dialog.setMinimumWidth(min_width)

    # Fonte base de acordo com as configurações (aplicada ao diálogo e filhos)
    try:
        values = app_settings.get_settings()
        font_family = str(values.get("UI_FONT_FAMILY") or "Segoe UI")
        font_size = int(values.get("UI_FONT_SIZE_PT") or 12)
    except Exception:
        font_family = "Segoe UI"
        font_size = 12
    base_font = QFont(font_family, pointSize=font_size)
    dialog.setFont(base_font)

    # Estilo visual
    dialog.setStyleSheet(
        f"""
        QDialog {{ background-color: #ffffff; }}
        QLabel {{ color: #2c3e50; }}
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {{
            padding: 6px; border: 1px solid #cfd8dc; border-radius: 4px; min-height: 28px;
        }}
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
            border-color: {PRIMARY_COLOR};
        }}
        QDialogButtonBox QPushButton {{ padding: 6px 12px; }}
        QDialogButtonBox QPushButton:default {{
            background-color: {PRIMARY_COLOR}; color: white; border-radius: 4px; border: 1px solid {PRIMARY_COLOR};
        }}
        QDialogButtonBox QPushButton:hover:default {{ background-color: #0a8a7d; }}
        QDialogButtonBox QPushButton:disabled {{ opacity: 0.6; }}
        """
    )

    # Margens/espacamentos do layout raiz
    layout: Optional[QLayout] = dialog.layout()
    if layout:
        layout.setContentsMargins(*content_margins)
        layout.setSpacing(spacing)


class DialogHeader(QWidget):
    """Cabeçalho padrão para diálogos com cor primaria e textos brancos."""

    def __init__(self, title: str, description: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("DialogHeader")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"""
            #DialogHeader {{ background-color: {PRIMARY_COLOR}; }}
            #DialogHeader QLabel#Title {{ color: white; font-size: 16px; font-weight: 600; }}
            #DialogHeader QLabel#Desc {{ color: white; opacity: .9; }}
            """
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(4)
        # Fonte base do sistema/tema
        try:
            values = app_settings.get_settings()
            font_family = str(values.get("UI_FONT_FAMILY") or "Segoe UI")
            font_size = int(values.get("UI_FONT_SIZE_PT") or 12)
        except Exception:
            font_family = "Segoe UI"
            font_size = 12

        lbl_title = QLabel(title, self)
        lbl_title.setObjectName("Title")
        f_title = QFont(font_family, pointSize=font_size + 2)
        f_title.setBold(True)
        lbl_title.setFont(f_title)
        lbl_desc = QLabel(description or "", self)
        lbl_desc.setObjectName("Desc")
        f_desc = QFont(font_family, pointSize=font_size)
        lbl_desc.setFont(f_desc)
        lbl_desc.setWordWrap(True)
        lay.addWidget(lbl_title)
        if description:
            lay.addWidget(lbl_desc)


# -------- Tema global --------

_LIGHT_CSS = """
QMainWindow, QWidget { background-color: #f2f5f7; color: #2c3e50; }
QMenuBar, QMenu { background-color: #eef2f4; color: #2c3e50; }
QStatusBar { background-color: #eef2f4; }
QTabWidget::pane { border-top: 1px solid #cfd8dc; }
QToolButton { color: #2c3e50; }
"""

_DARK_CSS = """
QMainWindow, QWidget { background-color: #202a2e; color: #e6eef2; }
QMenuBar, QMenu { background-color: #263238; color: #e6eef2; }
QStatusBar { background-color: #263238; color: #e6eef2; }
QTabWidget::pane { border-top: 1px solid #37474f; }
QToolButton { color: #e6eef2; }
"""


def set_app_theme(theme: str) -> None:
    app = QApplication.instance()
    if not app:
        return
    normalized = (theme or "system").lower()
    if normalized == "system":
        # Não aplica stylesheet global; mantém aparência nativa
        app.setStyleSheet("")
        return
    css = _LIGHT_CSS if normalized == "light" else _DARK_CSS
    app.setStyleSheet(css)


def toggle_app_theme() -> str:
    current = (app_settings.get_settings().get("UI_THEME") or "system").lower()
    new_theme = "dark" if current != "dark" else "system"
    values = app_settings.get_settings()
    values["UI_THEME"] = new_theme
    app_settings.save_settings(values)
    set_app_theme(new_theme)
    return new_theme


# -------- Fonte global (para MainWindow / Abas / Tabelas) --------

def get_base_font() -> QFont:
    try:
        values = app_settings.get_settings()
        family = str(values.get("UI_FONT_FAMILY") or "Segoe UI")
        size = int(values.get("UI_FONT_SIZE_PT") or 12)
    except Exception:
        family, size = "Segoe UI", 12
    return QFont(family, pointSize=size)


def apply_app_font(widget: QWidget) -> None:
    widget.setFont(get_base_font())


