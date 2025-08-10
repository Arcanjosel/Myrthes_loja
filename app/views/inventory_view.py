from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QSpinBox,
)

from app.utils.firebase_repository import FirebaseRepository


class InventoryView(QWidget):
    def __init__(self, repository: FirebaseRepository | None = None):
        super().__init__()
        self._repository = repository

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["ID", "Nome", "Unidade", "Quantidade"])
        self._table.horizontalHeader().setStretchLastSection(True)

        self._id = QLineEdit()
        self._name = QLineEdit()
        self._unit = QLineEdit()
        self._qty = QSpinBox()
        self._qty.setRange(-1_000_000, 1_000_000)

        self._btn_upsert = QPushButton("Salvar Item")
        self._btn_adjust_plus = QPushButton("+1")
        self._btn_adjust_minus = QPushButton("-1")

        form = QHBoxLayout()
        form.addWidget(QLabel("ID:"))
        form.addWidget(self._id)
        form.addWidget(QLabel("Nome:"))
        form.addWidget(self._name)
        form.addWidget(QLabel("Unidade:"))
        form.addWidget(self._unit)
        form.addWidget(QLabel("Qtde:"))
        form.addWidget(self._qty)
        form.addWidget(self._btn_upsert)
        form.addWidget(self._btn_adjust_plus)
        form.addWidget(self._btn_adjust_minus)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self._table)
        self.setLayout(layout)

        self._btn_upsert.clicked.connect(self._on_upsert)
        self._btn_adjust_plus.clicked.connect(lambda: self._on_adjust(1))
        self._btn_adjust_minus.clicked.connect(lambda: self._on_adjust(-1))

        self.reload()

    def _on_upsert(self) -> None:
        if not self._repository:
            return
        item_id = self._id.text().strip()
        name = self._name.text().strip()
        unit = self._unit.text().strip() or "un"
        qty = int(self._qty.value())
        if not item_id or not name:
            return
        self._repository.upsert_inventory_item(item_id, name, unit, qty)
        self.reload()

    def _on_adjust(self, delta: int) -> None:
        if not self._repository:
            return
        item_id = self._id.text().strip()
        if not item_id:
            return
        self._repository.adjust_inventory(item_id, delta)
        self.reload()

    def reload(self) -> None:
        if not self._repository:
            self._table.setRowCount(0)
            return
        items = self._repository.list_inventory()
        self._table.setRowCount(len(items))
        for r, (iid, name, unit, qty) in enumerate(items):
            self._table.setItem(r, 0, QTableWidgetItem(iid))
            self._table.setItem(r, 1, QTableWidgetItem(name))
            self._table.setItem(r, 2, QTableWidgetItem(unit))
            self._table.setItem(r, 3, QTableWidgetItem(str(qty)))
        self._table.resizeColumnsToContents()
