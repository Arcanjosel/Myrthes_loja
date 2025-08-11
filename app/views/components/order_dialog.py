from __future__ import annotations

from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)
from app.views.components.dialog_theme import apply_dialog_theme, DialogHeader

from app.controllers.client_controller import ClientController
from app.controllers.orders_controller import OrdersController
from app.controllers.service_controller import ServiceController
from app.models.client import Client
from app.models.order import OrderItem
from app.utils.icons_manager import IconManager
from app.views.components.service_item_dialog import ServiceItemDialog


class OrderDialog(QDialog):
    def __init__(self, parent, clients: ClientController, services: ServiceController, orders: OrdersController):
        super().__init__(parent)
        self.setWindowTitle("Novo Pedido")
        self.setModal(True)
        self.resize(820, 560)
        self._clients = clients
        self._services = services
        self._orders = orders

        self._client_search = QLineEdit()
        self._client_search.setPlaceholderText("Buscar cliente...")
        self._client_combo = QComboBox()

        self._due_date = QDateEdit()
        self._due_date.setCalendarPopup(True)
        self._due_date.setDate(date.today())

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["Serviço", "Tipo", "Subtipo", "Qtd", "Preço (R$)"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._btn_add_item = QPushButton(IconManager.get_icon("adicionar"), "Adicionar serviço")
        self._btn_remove_item = QPushButton(IconManager.get_icon("excluir"), "Remover")

        self._payment_mode = QComboBox()
        self._payment_mode.addItems(["Pagar depois", "Pagar 50% agora", "Pagar tudo agora"])

        self._print_after = QCheckBox("Imprimir recibo ao salvar")

        form_top = QFormLayout()
        form_top.addRow("Cliente:", self._client_combo)
        form_top.addRow("Filtrar:", self._client_search)
        form_top.addRow("Prazo:", self._due_date)
        form_top.addRow("Pagamento:", self._payment_mode)
        form_top.addRow("Opções:", self._print_after)

        btns_items = QHBoxLayout()
        btns_items.addWidget(self._btn_add_item)
        btns_items.addWidget(self._btn_remove_item)
        btns_items.addStretch(1)

        vbox = QVBoxLayout(self)
        vbox.addWidget(DialogHeader("Novo Pedido", "Escolha o cliente, defina prazo, itens e condição de pagamento."))
        vbox.addLayout(form_top)
        vbox.addLayout(btns_items)
        vbox.addWidget(self._table)

        self._lbl_total = QLabel("Total: R$ 0,00")
        bottom_bar = QHBoxLayout()
        bottom_bar.addWidget(self._lbl_total)
        bottom_bar.addStretch(1)

        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        ok_btn = self._buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setDefault(True)
        ok_btn.setEnabled(False)
        bottom_bar.addWidget(self._buttons)
        vbox.addLayout(bottom_bar)

        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)
        self._btn_add_item.clicked.connect(self._on_add_item)
        self._btn_remove_item.clicked.connect(self._on_remove_item)
        self._client_search.textChanged.connect(self._reload_clients)
        self._table.itemChanged.connect(self._recompute_total)

        self._reload_clients()
        self._recompute_total()
        apply_dialog_theme(self, min_width=820)

    def _on_accept(self) -> None:
        if not self.selected_client_id():
            self._client_combo.setFocus()
            return
        if not self.selected_items():
            self._btn_add_item.setFocus()
            return
        self.accept()

    def _reload_clients(self) -> None:
        q = self._client_search.text().strip()
        clients = self._clients.search(q) if q else self._clients.list()
        self._client_combo.clear()
        for c in clients:
            self._client_combo.addItem(f"{c.name} — {c.phone or ''}", c)

    def _on_add_item(self) -> None:
        dlg = ServiceItemDialog(self, self._services)
        if dlg.exec() == dlg.DialogCode.Accepted:
            item = dlg.result_item()
            if item:
                r = self._table.rowCount()
                self._table.insertRow(r)
                self._table.setItem(r, 0, QTableWidgetItem(item.service_name))
                self._table.setItem(r, 1, QTableWidgetItem(item.service_type))
                self._table.setItem(r, 2, QTableWidgetItem(item.service_subtype or "-"))
                self._table.setItem(r, 3, QTableWidgetItem(str(item.quantity)))
                self._table.setItem(r, 4, QTableWidgetItem(f"{(item.unit_price_cents*item.quantity)/100:.2f}"))
                self._table.item(r, 0).setData(Qt.ItemDataRole.UserRole, item)
                self._recompute_total()

    def _on_remove_item(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        for m in sorted(rows, key=lambda x: x.row(), reverse=True):
            self._table.removeRow(m.row())
        self._recompute_total()

    def selected_items(self) -> list[OrderItem]:
        items: list[OrderItem] = []
        for r in range(self._table.rowCount()):
            it = self._table.item(r, 0).data(Qt.ItemDataRole.UserRole)
            items.append(it)
        return items

    def selected_client(self) -> Client | None:
        idx = self._client_combo.currentIndex()
        if idx < 0:
            return None
        c = self._client_combo.itemData(idx)
        return c

    def selected_client_id(self) -> str | None:
        c = self.selected_client()
        return getattr(c, "id", None) if c else None

    def selected_due_date_iso(self) -> str:
        return self._due_date.date().toString("yyyy-MM-dd")

    def selected_payment_mode(self) -> str:
        return self._payment_mode.currentText()

    def should_print(self) -> bool:
        return self._print_after.isChecked()

    # --- UX helpers ---
    def _recompute_total(self) -> None:
        total = 0.0
        for r in range(self._table.rowCount()):
            try:
                qty = int(self._table.item(r, 3).text())
                price = float(self._table.item(r, 4).text().replace(",", "."))
                total += price
            except Exception:
                pass
        self._lbl_total.setText(f"Total: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        ok_btn = self._buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setEnabled(self._client_combo.count() > 0 and self._table.rowCount() > 0)
