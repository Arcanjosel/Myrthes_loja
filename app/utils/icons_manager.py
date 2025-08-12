"""
Gerenciador de Ícones (Tabler Icons) para PyQt6
"""

from PyQt6.QtGui import QIcon, QPixmap, QImage
from pytablericons import TablerIcons, OutlineIcon
from PIL import Image


class IconManager:
    ICON_MAP = {
        "adicionar": OutlineIcon.PLUS,
        "editar": OutlineIcon.EDIT,
        "excluir": OutlineIcon.TRASH,
        "buscar": OutlineIcon.SEARCH,
        "pedido": OutlineIcon.RECEIPT,
        "clientes": OutlineIcon.USERS,
        "servicos": OutlineIcon.TOOLS,
        "imprimir": OutlineIcon.PRINTER,
        "refresh": OutlineIcon.REFRESH,
        "toggle": OutlineIcon.SWITCH,
        "sair": OutlineIcon.LOGOUT,
        "lista": OutlineIcon.LIST,
        "config": OutlineIcon.SETTINGS,
        "dashboard": OutlineIcon.CHART_BAR,
    }

    @classmethod
    def get_icon(cls, icon_name: str, size: int = 20, color: str = "#2c3e50") -> QIcon:
        icon_enum = cls.ICON_MAP.get(icon_name, OutlineIcon.HELP)
        pil_image = TablerIcons.load(icon_enum, size=size, color=color)
        return QIcon(cls._pil_to_qpixmap(pil_image))

    @staticmethod
    def _pil_to_qpixmap(pil_image: Image.Image) -> QPixmap:
        if pil_image.mode != "RGBA":
            pil_image = pil_image.convert("RGBA")
        qimage = QImage(
            pil_image.tobytes("raw", "RGBA"),
            pil_image.width,
            pil_image.height,
            QImage.Format.Format_RGBA8888,
        )
        return QPixmap.fromImage(qimage) 