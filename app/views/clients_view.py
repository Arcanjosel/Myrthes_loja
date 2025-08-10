from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut, QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from app.config.settings import UI_TABLE_ROW_HEIGHT, UI_FONT_SIZE_PT
from app.controllers.client_controller import ClientController
from app.events.bus import bus
from app.models.client import Client
from app.utils.icons_manager import IconManager
from app.views.components.client_dialog import ClientDialog


class ClientsView(QWidget):
    def __init__(self, controller: ClientController):
        super().__init__()
        self._controller = controller

        # Barra de ações em linha
        self._btn_new = QPushButton(IconManager.get_icon("adicionar"), "Novo Cliente")
        self._search = QLineEdit()
        self._search.setPlaceholderText("Buscar por nome ou telefone...")
        self._btn_search = QPushButton(IconManager.get_icon("buscar"), "Buscar")

        actions = QHBoxLayout()
        actions.addWidget(self._btn_new)
        actions.addStretch(1)
        actions.addWidget(self._search)
        actions.addWidget(self._btn_search)

        # Tabela
        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Nome", "Telefone", "Observações"])
        self._table.setSelectionBehavior(self._table.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        header_font = QFont()
        header_font.setPointSize(UI_FONT_SIZE_PT + 1)
        self._table.horizontalHeader().setFont(header_font)

        layout = QVBoxLayout(self)
        layout.addLayout(actions)
        layout.addWidget(self._table)
        self.setLayout(layout)

        self._btn_new.clicked.connect(self._on_new_client)
        self._btn_search.clicked.connect(self._on_search)
        self._search.textChanged.connect(self._on_search)

        # Atalhos
        QShortcut(QKeySequence("Ctrl+N"), self, self._on_new_client)
        QShortcut(QKeySequence("Ctrl+F"), self, lambda: self._search.setFocus())

        self._reload()

    def _on_new_client(self) -> None:
        dlg = ClientDialog(self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        name, phone, notes = dlg.values()
        self._controller.upsert(name, phone or "", notes or "")
        bus.client_list_changed.emit()
        self._reload()

    def _on_search(self) -> None:
        query = self._search.text()
        clients = self._controller.search(query)
        self._populate(clients)

    def _reload(self) -> None:
        self._populate(self._controller.list())

    def _populate(self, clients: list[Client]) -> None:
        self._table.setRowCount(len(clients))
        for r, c in enumerate(clients):
            self._table.setItem(r, 0, QTableWidgetItem(c.name))
            self._table.setItem(r, 1, QTableWidgetItem(c.phone or "-"))
            self._table.setItem(r, 2, QTableWidgetItem(c.notes or "-"))
            self._table.setRowHeight(r, UI_TABLE_ROW_HEIGHT)
        self._table.resizeColumnsToContents()
