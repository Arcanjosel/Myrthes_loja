from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLabel

from app.models.service import Service


class ServiceEditorDialog(QDialog):
    def __init__(self, parent, service: Service):
        super().__init__(parent)
        self.setWindowTitle("Editar preço do serviço")
        self._service = service

        self._price_input = QDoubleSpinBox(self)
        self._price_input.setSuffix(" R$")
        self._price_input.setMaximum(1_000_000)
        self._price_input.setDecimals(2)
        self._price_input.setValue(service.price_cents / 100.0)

        form = QFormLayout()
        form.addRow(QLabel(f"Serviço: {service.name}"))
        form.addRow(QLabel(f"Tipo: {service.type}"))
        if service.subtype:
            form.addRow(QLabel(f"Subtipo: {service.subtype}"))
        form.addRow("Preço:", self._price_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        form.addRow(buttons)
        self.setLayout(form)

    def new_price_cents(self) -> int:
        return int(round(self._price_input.value() * 100))
