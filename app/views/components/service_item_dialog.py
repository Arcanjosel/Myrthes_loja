from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QSpinBox,
)

from app.controllers.service_controller import ServiceController
from app.models.order import OrderItem


class ServiceItemDialog(QDialog):
    def __init__(self, parent, service_controller: ServiceController):
        super().__init__(parent)
        self.setWindowTitle("Adicionar serviço ao pedido")
        self._svc_ctrl = service_controller
        self._services = self._svc_ctrl.list_services()

        self._combo = QComboBox(self)
        for s in self._services:
            label = f"{s.name} — {s.subtype or s.type} (R$ {s.price_cents/100:.2f})"
            self._combo.addItem(label, s)

        self._qty = QSpinBox(self)
        self._qty.setMinimum(1)
        self._qty.setMaximum(999)
        self._qty.setValue(1)

        form = QFormLayout()
        form.addRow("Serviço:", self._combo)
        form.addRow("Quantidade:", self._qty)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)
        self.setLayout(form)

    def result_item(self) -> OrderItem | None:
        idx = self._combo.currentIndex()
        if idx < 0:
            return None
        svc = self._combo.itemData(idx)
        qty = int(self._qty.value())
        return OrderItem(
            service_name=svc.name,
            service_type=svc.type,
            service_subtype=svc.subtype,
            unit_price_cents=int(svc.price_cents),
            quantity=qty,
        )
