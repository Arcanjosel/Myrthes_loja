from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from app.controllers.client_controller import ClientController
from app.models.client import Client


class ClientsView(QWidget):
    def __init__(self, controller: ClientController):
        super().__init__()
        self._controller = controller

        # Formulário
        self._name = QLineEdit()
        self._phone = QLineEdit()
        self._phone.setInputMask("(00) 00000-0000;_")
        self._notes = QTextEdit()
        self._btn_save = QPushButton("Salvar cliente")
        self._btn_new = QPushButton("Limpar")

        form = QVBoxLayout()
        form.addWidget(QLabel("Nome:"))
        form.addWidget(self._name)
        form.addWidget(QLabel("Telefone:"))
        form.addWidget(self._phone)
        form.addWidget(QLabel("Observações:"))
        form.addWidget(self._notes)

        btns = QHBoxLayout()
        btns.addWidget(self._btn_save)
        btns.addWidget(self._btn_new)
        btns.addStretch(1)
        form.addLayout(btns)

        # Busca e lista
        self._search = QLineEdit()
        self._search.setPlaceholderText("Buscar por nome ou telefone...")
        self._btn_search = QPushButton("Buscar")
        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Nome", "Telefone", "Observações"])
        self._table.setSelectionBehavior(self._table.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)

        search_row = QHBoxLayout()
        search_row.addWidget(self._search)
        search_row.addWidget(self._btn_search)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(QLabel("Clientes cadastrados"))
        layout.addLayout(search_row)
        layout.addWidget(self._table)
        self.setLayout(layout)

        self._btn_save.clicked.connect(self._on_save)
        self._btn_new.clicked.connect(self._on_new)
        self._btn_search.clicked.connect(self._on_search)
        self._search.textChanged.connect(self._on_search)
        self._table.itemSelectionChanged.connect(self._on_table_selection)

        self._reload()

    def _on_save(self) -> None:
        name = self._name.text().strip()
        if not name:
            return
        phone = self._phone.text().strip()
        notes = self._notes.toPlainText().strip()
        self._controller.upsert(name, phone, notes)
        self._on_new()
        self._reload()

    def _on_new(self) -> None:
        self._name.clear()
        self._phone.clear()
        self._notes.clear()
        self._name.setFocus()
        self._table.clearSelection()

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
            self._table.item(r, 0).setData(Qt.ItemDataRole.UserRole, c)
        self._table.resizeColumnsToContents()

    def _on_table_selection(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return
        row = rows[0].row()
        c: Client = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self._name.setText(c.name)
        self._phone.setText(c.phone or "")
        self._notes.setText(c.notes or "")
