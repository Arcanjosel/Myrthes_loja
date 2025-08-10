from __future__ import annotations

from datetime import date
import os

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
    QDateEdit,
)

from app.config.settings import (
    THERMAL_PRINTER_VENDOR_ID,
    THERMAL_PRINTER_PRODUCT_ID,
    THERMAL_PRINTER_SERIAL_PORT,
    THERMAL_PRINTER_BAUDRATE,
    THERMAL_PRINTER_HOST,
)
from app.controllers.client_controller import ClientController
from app.controllers.orders_controller import OrdersController
from app.controllers.service_controller import ServiceController
from app.models.order import OrderItem
from app.views.components.service_item_dialog import ServiceItemDialog
from app.views.components.qr_barcode_utils import generate_qr_png, generate_barcode_png
from app.views.components.thermal_printer import ThermalPrinter


class OrdersView(QWidget):
    def __init__(self, client_controller: ClientController, service_controller: ServiceController, orders_controller: OrdersController):
        super().__init__()
        self._client_ctrl = client_controller
        self._service_ctrl = service_controller
        self._orders_ctrl = orders_controller

        # Cliente
        self._client_search = QLineEdit()
        self._client_search.setPlaceholderText("Filtrar cliente por nome ou telefone...")
        self._client_combo = QComboBox()

        # Prazo e status
        self._due_date = QDateEdit()
        self._due_date.setCalendarPopup(True)
        self._due_date.setDate(date.today())
        self._status_combo = QComboBox()
        self._status_combo.addItems(["aberto", "pronto", "entregue"])

        # Itens
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["Serviço", "Tipo", "Subtipo", "Qtd", "Preço (R$)"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._btn_add_item = QPushButton("Adicionar serviço")
        self._btn_remove_item = QPushButton("Remover selecionado")

        # Total e ações
        self._total_label = QLabel("Total: R$ 0,00")
        self._btn_save = QPushButton("Salvar pedido")
        self._btn_print = QPushButton("Imprimir recibo")

        layout = QVBoxLayout(self)

        # Cliente UI
        client_row = QHBoxLayout()
        client_row.addWidget(QLabel("Cliente:"))
        client_row.addWidget(self._client_combo, 2)
        client_row.addWidget(self._client_search, 1)
        layout.addLayout(client_row)

        # Prazo/Status
        meta_row = QHBoxLayout()
        meta_row.addWidget(QLabel("Prazo:"))
        meta_row.addWidget(self._due_date)
        meta_row.addWidget(QLabel("Status:"))
        meta_row.addWidget(self._status_combo)
        meta_row.addStretch(1)
        layout.addLayout(meta_row)

        # Itens UI
        btn_row = QHBoxLayout()
        btn_row.addWidget(self._btn_add_item)
        btn_row.addWidget(self._btn_remove_item)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)
        layout.addWidget(self._table)

        # Total/Salvar
        bottom = QHBoxLayout()
        bottom.addWidget(self._total_label)
        bottom.addStretch(1)
        bottom.addWidget(self._btn_print)
        bottom.addWidget(self._btn_save)
        layout.addLayout(bottom)

        self.setLayout(layout)

        self._btn_add_item.clicked.connect(self._on_add_item)
        self._btn_remove_item.clicked.connect(self._on_remove_item)
        self._btn_save.clicked.connect(self._on_save)
        self._btn_print.clicked.connect(self._on_print)
        self._client_search.textChanged.connect(self._reload_clients)

        self._reload_clients()

    def _reload_clients(self) -> None:
        query = self._client_search.text().strip()
        clients = self._client_ctrl.search(query) if query else self._client_ctrl.list()
        self._client_combo.clear()
        for c in clients:
            label = f"{c.name} — {c.phone or ''}"
            self._client_combo.addItem(label, c)

    def _on_add_item(self) -> None:
        dlg = ServiceItemDialog(self, self._service_ctrl)
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
                self._recalc_total()

    def _on_remove_item(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        for m in sorted(rows, key=lambda x: x.row(), reverse=True):
            self._table.removeRow(m.row())
        self._recalc_total()

    def _on_save(self) -> None:
        idx = self._client_combo.currentIndex()
        if idx < 0:
            return
        client = self._client_combo.itemData(idx)
        items: list[OrderItem] = []
        for r in range(self._table.rowCount()):
            it = self._table.item(r, 0).data(Qt.ItemDataRole.UserRole)
            items.append(it)
        if not items:
            return
        due_iso = self._due_date.date().toString("yyyy-MM-dd")
        order = self._orders_ctrl.create_order(client.id, items, due_date_iso=due_iso)
        if self._status_combo.currentText() != "aberto":
            self._orders_ctrl.update_status(order.id, self._status_combo.currentText(), None)
        self._last_order_code = order.order_code if hasattr(order, 'order_code') else None
        self._table.setRowCount(0)
        self._recalc_total()

    def _on_print(self) -> None:
        idx = self._client_combo.currentIndex()
        if idx < 0:
            return
        client = self._client_combo.itemData(idx)
        # total atual
        total_cents = 0
        items_text = []
        for r in range(self._table.rowCount()):
            it: OrderItem = self._table.item(r, 0).data(Qt.ItemDataRole.UserRole)
            total_cents += it.unit_price_cents * it.quantity
            price = (it.unit_price_cents * it.quantity) / 100.0
            items_text.append(f"- {it.service_name} ({it.service_subtype or it.service_type}) x{it.quantity} — R$ {price:.2f}")
        header = [
            "Myrthes Costuras",
            f"Cliente: {client.name} — {client.phone or ''}",
            f"Prazo: {self._due_date.date().toString('dd/MM/yyyy')}  Status: {self._status_combo.currentText()}",
            "",
        ]
        footer = [
            "-",
            f"Total: R$ {total_cents/100:.2f}",
        ]
        code_line = []
        qr_path = bc_path = None
        if hasattr(self, "_last_order_code") and self._last_order_code:
            from app.views.components.qr_barcode_utils import generate_qr_png, generate_barcode_png
            qr_path = generate_qr_png(self._last_order_code)
            bc_path = generate_barcode_png(self._last_order_code)
            code_line = [
                "",
                f"Código do Pedido: {self._last_order_code}",
            ]
        # Tenta impressora térmica
        printer = ThermalPrinter(
            usb=(THERMAL_PRINTER_VENDOR_ID, THERMAL_PRINTER_PRODUCT_ID) if THERMAL_PRINTER_VENDOR_ID and THERMAL_PRINTER_PRODUCT_ID else None,
            serial_port=THERMAL_PRINTER_SERIAL_PORT,
            host=THERMAL_PRINTER_HOST,
            baudrate=THERMAL_PRINTER_BAUDRATE,
        )
        if printer.available():
            txt = "\n".join(header + items_text + footer + code_line) + "\n\n"
            ok = printer.print_text(txt)
            if ok and qr_path:
                printer.print_image(qr_path)
            if ok and bc_path:
                printer.print_image(bc_path)
            printer.cut()
            return
        # Fallback: recibo.txt
        lines = header + items_text + footer
        if code_line:
            lines += code_line + [f"QR: {os.path.abspath(qr_path)}", f"Barcode: {os.path.abspath(bc_path)}", "(Use um app de QR/código de barras no celular para identificar o pedido)"]
        text = "\n".join(lines)
        with open("recibo.txt", "w", encoding="utf-8") as f:
            f.write(text)

    def _recalc_total(self) -> None:
        total_cents = 0
        for r in range(self._table.rowCount()):
            it: OrderItem = self._table.item(r, 0).data(Qt.ItemDataRole.UserRole)
            total_cents += it.unit_price_cents * it.quantity
        value = total_cents / 100.0
        s = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        self._total_label.setText(f"Total: R$ {s}")
