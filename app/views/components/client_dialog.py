from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
)
from app.views.components.dialog_theme import apply_dialog_theme, DialogHeader


class ClientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Novo Cliente")
        self.setModal(True)
        self.setMinimumWidth(420)

        self._name = QLineEdit()
        self._name.setPlaceholderText("Obrigatório")
        self._phone = QLineEdit()
        self._phone.setInputMask("(00) 00000-0000;_")
        self._phone.setPlaceholderText("Opcional")
        self._notes = QTextEdit()
        self._notes.setPlaceholderText("Observações, medidas, preferências...")

        form = QFormLayout()
        form.addRow("Nome:", self._name)
        form.addRow("Telefone:", self._phone)
        form.addRow("Observações:", self._notes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_btn.setDefault(True)
        self._ok_btn.setEnabled(False)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        # Layout raiz com header
        from PyQt6.QtWidgets import QVBoxLayout
        root = QVBoxLayout(self)
        root.addWidget(DialogHeader("Novo Cliente", "Cadastre ou edite um cliente com dados básicos para identificação."))
        root.addLayout(form)
        self.setLayout(root)
        apply_dialog_theme(self, min_width=500)
        self._name.textChanged.connect(self._validate)
        self._validate()
        self._name.setFocus(Qt.FocusReason.ActiveWindowFocusReason)

    def _on_accept(self) -> None:
        if not self._name.text().strip():
            self._name.setFocus()
            return
        self.accept()

    def _validate(self) -> None:
        valid = bool(self._name.text().strip())
        self._ok_btn.setEnabled(valid)

    def values(self) -> tuple[str, str | None, str | None]:
        name = self._name.text().strip()
        phone = self._phone.text().strip() or None
        notes = self._notes.toPlainText().strip() or None
        return name, phone, notes
