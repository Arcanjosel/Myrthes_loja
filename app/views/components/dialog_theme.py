from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDialog, QLayout, QWidget, QVBoxLayout, QLabel


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
        lbl_title = QLabel(title, self)
        lbl_title.setObjectName("Title")
        lbl_desc = QLabel(description or "", self)
        lbl_desc.setObjectName("Desc")
        lbl_desc.setWordWrap(True)
        lay.addWidget(lbl_title)
        if description:
            lay.addWidget(lbl_desc)


