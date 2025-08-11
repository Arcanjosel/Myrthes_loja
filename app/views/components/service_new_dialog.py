from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
)
from app.views.components.dialog_theme import apply_dialog_theme, DialogHeader


class ServiceNewDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Novo Serviço")
        self.setModal(True)
        self.setMinimumWidth(420)

        self._name = QLineEdit()
        self._name.setPlaceholderText("Obrigatório")
        self._type = QComboBox()
        self._type.setEditable(True)
        self._type.addItems(["ajuste_tamanho", "troca_ziper", "barra", "pence"])  # sugestões
        self._subtype = QLineEdit()

        self._price_brl = QDoubleSpinBox()
        self._price_brl.setDecimals(2)
        self._price_brl.setMaximum(1_000_000)
        self._price_brl.setPrefix("R$ ")
        self._price_brl.setSingleStep(1.00)

        form = QFormLayout()
        form.addRow("Nome:", self._name)
        form.addRow("Tipo:", self._type)
        form.addRow("Subtipo:", self._subtype)
        form.addRow("Preço:", self._price_brl)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self._ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_btn.setDefault(True)
        self._ok_btn.setEnabled(False)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)
        from PyQt6.QtWidgets import QVBoxLayout
        root = QVBoxLayout(self)
        root.addWidget(DialogHeader("Novo Serviço", "Cadastre serviços com tipo, subtipo e preço para uso nos pedidos."))
        root.addLayout(form)
        self._name.textChanged.connect(self._validate)
        self._type.editTextChanged.connect(self._validate)
        self._price_brl.valueChanged.connect(self._validate)
        self._validate()
        self._name.setFocus()
        apply_dialog_theme(self, min_width=500)

    def _on_accept(self) -> None:
        if not self._name.text().strip():
            self._name.setFocus()
            return
        if not self._type.currentText().strip():
            self._type.setEditText("")
            self._type.setFocus()
            return
        self.accept()

    def values(self) -> tuple[str, str, str | None, int]:
        name = self._name.text().strip()
        type_ = self._type.currentText().strip()
        subtype = self._subtype.text().strip() or None
        price_cents = int(round(self._price_brl.value() * 100))
        return name, type_, subtype, price_cents

    def _validate(self) -> None:
        valid = bool(self._name.text().strip()) and bool(self._type.currentText().strip()) and self._price_brl.value() > 0
        self._ok_btn.setEnabled(valid)
