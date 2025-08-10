from __future__ import annotations

from datetime import datetime, timezone

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from app.controllers.orders_controller import OrdersController


class OrdersListView(QWidget):
    def __init__(self, orders_controller: OrdersController):
        super().__init__()
        self._orders_ctrl = orders_controller

        self._status = QComboBox()
        self._status.addItems(["todos", "aberto", "pronto", "entregue"])
        self._q_client = QLineEdit()
        self._q_client.setPlaceholderText("Cliente/telefone...")
        self._q_code = QLineEdit()
        self._q_code.setPlaceholderText("Código do pedido (QR/Barcode)...")
        self._btn_search = QPushButton("Buscar")
        self._btn_mark_delivered = QPushButton("Marcar entregue")

        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(["Código", "Cliente", "Status", "Total (R$)", "Prazo", "ID"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        filters = QHBoxLayout()
        filters.addWidget(QLabel("Status:"))
        filters.addWidget(self._status)
        filters.addWidget(QLabel("Cliente:"))
        filters.addWidget(self._q_client)
        filters.addWidget(QLabel("Código:"))
        filters.addWidget(self._q_code)
        filters.addWidget(self._btn_search)

        actions = QHBoxLayout()
        actions.addWidget(self._btn_mark_delivered)
        actions.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(filters)
        layout.addLayout(actions)
        layout.addWidget(self._table)
        self.setLayout(layout)

        self._btn_search.clicked.connect(self._reload)
        self._q_client.returnPressed.connect(self._reload)
        self._q_code.returnPressed.connect(self._reload)
        self._btn_mark_delivered.clicked.connect(self._mark_delivered)

        self._reload()

    def _reload(self) -> None:
        status = self._status.currentText()
        q_client = self._q_client.text().strip()
        q_code = self._q_code.text().strip()
        rows = self._orders_ctrl.list_orders(status if status != "todos" else None, q_client or None, q_code or None)
        self._table.setRowCount(len(rows))
        for r, (oid, code, client_name, status, total_cents, due) in enumerate(rows):
            self._table.setItem(r, 0, QTableWidgetItem(code or ""))
            self._table.setItem(r, 1, QTableWidgetItem(client_name or ""))
            self._table.setItem(r, 2, QTableWidgetItem(status))
            self._table.setItem(r, 3, QTableWidgetItem(f"{(total_cents/100):.2f}"))
            self._table.setItem(r, 4, QTableWidgetItem(due or ""))
            self._table.setItem(r, 5, QTableWidgetItem(oid))
            self._table.item(r, 0).setData(Qt.ItemDataRole.UserRole, oid)
        self._table.resizeColumnsToContents()

    def _mark_delivered(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return
        oid = self._table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        delivered_iso = datetime.now(timezone.utc).isoformat()
        self._orders_ctrl.update_status(oid, "entregue", delivered_iso)
        self._reload()
