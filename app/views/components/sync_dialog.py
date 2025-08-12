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
            "Modo offline: os dados são salvos no SQLite local.\n"
            "Este diálogo permite apenas limpar a fila local de sync caso exista."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self._cred_path = QLineEdit(self)
        self._cred_path.setReadOnly(True)
        form = QFormLayout()
        layout.addLayout(form)

        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

        # Ações locais
        self._btn_just_sync = QPushButton("Limpar fila local de sync", self)
        self._btn_just_sync.clicked.connect(self._on_just_sync)
        layout.addWidget(self._btn_just_sync)

        self._sync_manager = sync_manager
        apply_dialog_theme(self, min_width=520)

    def _on_sync(self) -> None:
        self.accept()

    def _on_just_sync(self) -> None:
        sent = 0
        try:
            # Limpa os registros da fila
            from app.data.sqlite import read_sync_batch, delete_sync_item
            batch = read_sync_batch(1000)
            for item_id, *_ in batch:
                delete_sync_item(item_id)
            sent = len(batch)
        except Exception:
            pass
        QMessageBox.information(self, "Sincronização", f"Itens removidos da fila local: {sent}")


