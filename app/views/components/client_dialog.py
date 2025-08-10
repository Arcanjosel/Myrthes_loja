from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
)


class ClientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Novo Cliente")

        self._name = QLineEdit()
        self._phone = QLineEdit()
        self._phone.setInputMask("(00) 00000-0000;_")
        self._notes = QTextEdit()

        form = QFormLayout(self)
        form.addRow("Nome:", self._name)
        form.addRow("Telefone:", self._phone)
        form.addRow("Observações:", self._notes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        self.setLayout(form)

    def _on_accept(self) -> None:
        if not self._name.text().strip():
            self._name.setFocus()
            return
        self.accept()

    def values(self) -> tuple[str, str | None, str | None]:
        name = self._name.text().strip()
        phone = self._phone.text().strip() or None
        notes = self._notes.toPlainText().strip() or None
        return name, phone, notes
