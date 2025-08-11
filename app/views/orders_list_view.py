from __future__ import annotations

from datetime import datetime, timezone, date
import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut, QFont
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
    QMessageBox,
    QDateEdit,
)

from app.config.settings import UI_TABLE_ROW_HEIGHT, UI_FONT_SIZE_PT
from app.controllers.client_controller import ClientController
from app.controllers.orders_controller import OrdersController
from app.controllers.service_controller import ServiceController
from app.utils.icons_manager import IconManager
from app.views.components.order_dialog import OrderDialog
from app.views.components.qr_barcode_utils import generate_qr_png, generate_barcode_png
from app.config import settings as app_settings


class OrdersListView(QWidget):
    def __init__(self, orders_controller: OrdersController, client_controller: ClientController, service_controller: ServiceController):
        super().__init__()
        self._orders_ctrl = orders_controller
        self._client_ctrl = client_controller
        self._service_ctrl = service_controller

        # Controles em uma linha (topo)
        self._btn_new_order = QPushButton(IconManager.get_icon("adicionar"), "Novo Pedido")
        self._status = QComboBox()
        self._status.addItems(["todos", "aberto", "pronto", "entregue"])
        self._q_client = QLineEdit()
        self._q_client.setPlaceholderText("Cliente/telefone...")
        self._q_code = QLineEdit()
        self._q_code.setPlaceholderText("Código do pedido (QR/Barcode)...")
        self._btn_search = QPushButton(IconManager.get_icon("buscar"), "Buscar")

        header = QHBoxLayout()
        header.addWidget(self._btn_new_order)
        header.addWidget(QLabel("Status:"))
        header.addWidget(self._status)
        header.addWidget(QLabel("Cliente:"))
        header.addWidget(self._q_client)
        header.addWidget(QLabel("Código:"))
        header.addWidget(self._q_code)
        header.addWidget(self._btn_search)
        header.addStretch(1)

        # Tabela
        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(["Código", "Cliente", "Status", "Total (R$)", "Prazo", "ID"])
        self._table.setSelectionBehavior(self._table.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionMode(self._table.SelectionMode.SingleSelection)
        header_font = QFont()
        header_font.setPointSize(UI_FONT_SIZE_PT + 1)
        self._table.horizontalHeader().setFont(header_font)

        # Barra inferior com ações do dia e entrega
        self._closing_date = QDateEdit()
        self._closing_date.setCalendarPopup(True)
        self._closing_date.setDate(date.today())
        self._btn_cash_close = QPushButton("Fechar Caixa do Dia")
        self._btn_mark_delivered = QPushButton(IconManager.get_icon("adicionar"), "Marcar entregue")

        bottom_bar = QHBoxLayout()
        bottom_bar.addWidget(QLabel("Data:"))
        bottom_bar.addWidget(self._closing_date)
        bottom_bar.addWidget(self._btn_cash_close)
        bottom_bar.addStretch(1)
        bottom_bar.addWidget(self._btn_mark_delivered)

        layout = QVBoxLayout(self)
        layout.addLayout(header)
        layout.addWidget(self._table)
        layout.addLayout(bottom_bar)
        self.setLayout(layout)

        # Ligações
        self._btn_new_order.clicked.connect(self._on_new_order)
        self._btn_search.clicked.connect(self._reload)
        self._q_client.returnPressed.connect(self._reload)
        self._q_code.returnPressed.connect(self._reload)
        self._btn_mark_delivered.clicked.connect(self._mark_delivered)
        self._btn_cash_close.clicked.connect(self._on_cash_close)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

        # Atalhos (evita conflito do Ctrl+N com o menu)
        QShortcut(QKeySequence("Ctrl+D"), self, self._mark_delivered)
        QShortcut(QKeySequence("Return"), self, self._reload)

        self._reload()
        self._on_selection_changed()

    def open_new_order(self) -> None:
        self._on_new_order()

    def _on_new_order(self) -> None:
        dlg = OrderDialog(self, self._client_ctrl, self._service_ctrl, self._orders_ctrl)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        client = dlg.selected_client()
        client_id = dlg.selected_client_id()
        items = dlg.selected_items()
        if not client_id or not items:
            return
        due_iso = dlg.selected_due_date_iso()
        order = self._orders_ctrl.create_order(client_id, items, due_date_iso=due_iso)

        payment_mode = dlg.selected_payment_mode()
        total_cents = sum(i.unit_price_cents * i.quantity for i in items)
        if payment_mode == "Pagar 50% agora":
            self._orders_ctrl.add_payment(order.id, total_cents // 2, method="entrada", note="50%")
        elif payment_mode == "Pagar tudo agora":
            self._orders_ctrl.add_payment(order.id, total_cents, method="à vista", note="100%")

        if getattr(dlg, 'should_print', lambda: False)():
            self._print_receipt(client, items, total_cents, order.order_code)

        self._reload()
        QMessageBox.information(self, "Pedido criado", f"Pedido criado com total R$ {total_cents/100:.2f}.")

    def _print_receipt(self, client, items, total_cents: int, order_code: str | None) -> None:
        lines = []
        lines.append("Myrthes Costuras — Recibo de Pedido")
        lines.append(f"Cliente: {getattr(client,'name','')} — {getattr(client,'phone','') or ''}")
        lines.append("")
        for it in items:
            price = (it.unit_price_cents * it.quantity) / 100.0
            lines.append(f"- {it.service_name} ({it.service_subtype or it.service_type}) x{it.quantity} — R$ {price:.2f}")
        lines.append("-")
        lines.append(f"Total: R$ {total_cents/100:.2f}")

        qr_path = bc_path = None
        if order_code:
            qr_path = generate_qr_png(order_code)
            bc_path = generate_barcode_png(order_code)
            lines.append("")
            lines.append(f"Código do Pedido: {order_code}")

        try:
            from app.views.components.thermal_printer import ThermalPrinter
            vid = getattr(app_settings, "THERMAL_PRINTER_VENDOR_ID", None)
            pid = getattr(app_settings, "THERMAL_PRINTER_PRODUCT_ID", None)
            printer = ThermalPrinter(
                usb=(vid, pid) if vid and pid else None,
                serial_port=getattr(app_settings, "THERMAL_PRINTER_SERIAL_PORT", None),
                host=getattr(app_settings, "THERMAL_PRINTER_HOST", None),
                baudrate=int(getattr(app_settings, "THERMAL_PRINTER_BAUDRATE", 9600)),
            )
            if printer.available():
                printer.print_text("\n".join(lines) + "\n\n")
                if qr_path:
                    printer.print_image(qr_path)
                if bc_path:
                    printer.print_image(bc_path)
                printer.cut()
                return
        except Exception:
            pass

        if order_code and qr_path and bc_path:
            lines += [f"QR: {os.path.abspath(qr_path)}", f"Barcode: {os.path.abspath(bc_path)}", "(Use um app de QR/código de barras no celular para identificar o pedido)"]
        with open("recibo.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _on_cash_close(self) -> None:
        date_iso = self._closing_date.date().toString("yyyy-MM-dd")
        total_cents = self._orders_ctrl.cash_closing_sum_for_date(date_iso)
        QMessageBox.information(self, "Fechamento de Caixa", f"Data: {date_iso}\nTotal recebido: R$ {total_cents/100:.2f}")

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
            id_item = QTableWidgetItem(oid)
            id_item.setData(Qt.ItemDataRole.UserRole, oid)
            self._table.setItem(r, 5, id_item)
            self._table.setRowHeight(r, UI_TABLE_ROW_HEIGHT)
        self._table.resizeColumnsToContents()
        self._table.setColumnHidden(5, True)

    def _current_order_id(self) -> str | None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        item = self._table.item(row, 5)
        oid = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not oid and item:
            oid = item.text()
        return oid

    def _mark_delivered(self) -> None:
        oid = self._current_order_id()
        if not oid:
            QMessageBox.information(self, "Pedidos", "Selecione um pedido na tabela.")
            return
        delivered_iso = datetime.now(timezone.utc).isoformat()
        self._orders_ctrl.update_status(oid, "entregue", delivered_iso)
        self._reload()

    def _on_selection_changed(self) -> None:
        has_sel = bool(self._table.selectionModel().selectedRows())
        self._btn_mark_delivered.setEnabled(has_sel)
