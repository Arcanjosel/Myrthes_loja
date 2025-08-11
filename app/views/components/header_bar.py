from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QWidget, QToolButton

from app.utils.icons_manager import IconManager


class HeaderBar(QWidget):
    """Barra de cabeçalho com logo, título e ações à direita."""

    def __init__(self, title: str, actions: Iterable[Tuple[str, str, str, callable]], parent: QWidget | None = None):
        """Cria a barra.

        actions: iterável de tuplas (icon_name, tooltip, shortcut, on_trigger)
        """
        super().__init__(parent)

        # Estilo: fundo verde e texto branco
        self.setObjectName("HeaderBar")
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            """
            #HeaderBar { background-color: #007065; min-height: 56px; }
            QLabel#Title { color: white; font-size: 18px; font-weight: 600; }
            QLabel#Subtitle { color: white; }
            QToolButton { color: white; border: none; padding: 6px; }
            QToolButton:hover { background-color: rgba(255,255,255,0.12); border-radius: 6px; }
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # Logo
        logo = QLabel(self)
        logo.setObjectName("Logo")
        pix = self._load_logo_pixmap()
        if pix:
            logo.setPixmap(pix.scaledToHeight(44, Qt.TransformationMode.SmoothTransformation))
            logo.setFixedHeight(48)
        layout.addWidget(logo)

        # Título
        title_label = QLabel(title, self)
        title_label.setObjectName("Title")
        layout.addWidget(title_label)

        layout.addStretch(1)

        # Ações à direita
        for icon_name, tooltip, shortcut, handler in actions:
            btn = QToolButton(self)
            btn.setIcon(IconManager.get_icon(icon_name, size=22, color="#ffffff"))
            btn.setIconSize(QSize(22, 22))
            btn.setToolTip(f"{tooltip} ({shortcut})")
            btn.clicked.connect(handler)
            layout.addWidget(btn)

    @staticmethod
    def _load_logo_pixmap() -> QPixmap | None:
        try:
            project_root = Path(__file__).resolve().parents[3]
            search_dirs = [
                project_root,
                project_root / "assets",
                project_root / "app" / "assets",
                Path.cwd(),
            ]
            candidate_names = [
                "logo4.png",
                "logo2.png",
                "logo.png",
                "Logo4.png",
                "Logo2.png",
                "Logo.png",
            ]
            for d in search_dirs:
                for name in candidate_names:
                    p = d / name
                    if p.is_file():
                        return QPixmap(str(p))
        except Exception:
            pass
        return None

    # Garante a cor de fundo mesmo se stylesheet não aplicar
    def paintEvent(self, event):  # type: ignore[override]
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#007065"))
        super().paintEvent(event)


