from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.config import settings as app_settings
from app.views.components.dialog_theme import apply_dialog_theme, DialogHeader


class SyncDialog(QDialog):
    def __init__(self, parent, sync_manager, current_credentials: Optional[str] = None):
        super().__init__(parent)
        self.setWindowTitle("Sincronização com Firebase")
        self.setModal(True)
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        layout.addWidget(DialogHeader("Sincronização", "Informe o JSON de credenciais e envie a fila de atualizações ao Firebase."))

        info = QLabel(
            "Informe o caminho do arquivo de credenciais JSON do Firebase (service account).\n"
            "Ele será salvo em settings.json, e a sincronização será enviada agora."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self._cred_path = QLineEdit(self)
        self._cred_path.setPlaceholderText("ex.: C:/Users/voce/Downloads/credenciais.json")
        self._cred_path.setText(current_credentials or str(app_settings.get_settings().get("FIREBASE_CREDENTIALS") or ""))

        form = QFormLayout()
        form.addRow("Credenciais (JSON):", self._cred_path)
        layout.addLayout(form)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self._on_sync)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

        # Atalho visual para enviar sem salvar credenciais
        self._btn_just_sync = QPushButton("Sincronizar sem salvar caminho", self)
        self._btn_just_sync.clicked.connect(self._on_just_sync)
        layout.addWidget(self._btn_just_sync)

        self._sync_manager = sync_manager
        apply_dialog_theme(self, min_width=520)

    def _on_sync(self) -> None:
        path = self._cred_path.text().strip()
        values = app_settings.get_settings()
        values["FIREBASE_CREDENTIALS"] = path or None
        app_settings.save_settings(values)
        sent = self._sync_manager.flush_now()
        QMessageBox.information(self, "Sincronização", f"Envios aplicados: {sent}")
        self.accept()

    def _on_just_sync(self) -> None:
        sent = self._sync_manager.flush_now()
        QMessageBox.information(self, "Sincronização", f"Envios aplicados: {sent}")


