from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut, QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QCheckBox,
)

from app.config.settings import UI_TABLE_ROW_HEIGHT, UI_FONT_SIZE_PT
from app.controllers.service_controller import ServiceController
from app.models.service import Service
from app.utils.icons_manager import IconManager
from app.views.components.service_editor_dialog import ServiceEditorDialog
from app.views.components.service_new_dialog import ServiceNewDialog


class ServicesView(QWidget):
    def __init__(self, controller: ServiceController):
        super().__init__()
        self._controller = controller

        # Barra de ações em linha
        self._show_inactive = QCheckBox("Mostrar inativos")
        self._btn_refresh = QPushButton(IconManager.get_icon("refresh"), "Atualizar")
        self._btn_edit = QPushButton(IconManager.get_icon("editar"), "Editar preço")
        self._btn_toggle_active = QPushButton(IconManager.get_icon("toggle"), "Ativar/Desativar")
        self._btn_add = QPushButton(IconManager.get_icon("adicionar"), "Adicionar…")

        top_bar = QHBoxLayout()
        top_bar.addWidget(self._show_inactive)
        top_bar.addWidget(self._btn_refresh)
        top_bar.addWidget(self._btn_edit)
        top_bar.addWidget(self._btn_toggle_active)
        top_bar.addStretch(1)
        top_bar.addWidget(self._btn_add)

        # Tabela
        self._table = QTableWidget(self)
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Serviço", "Tipo", "Subtipo", "Preço", "Ativo"])
        self._table.setSelectionBehavior(self._table.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        header_font = QFont()
        header_font.setPointSize(UI_FONT_SIZE_PT + 1)
        self._table.horizontalHeader().setFont(header_font)
        # Larguras fixas/ mínimas para colunas curtas
        self._table.setColumnWidth(1, 120)  # Tipo
        self._table.setColumnWidth(2, 140)  # Subtipo
        self._table.setColumnWidth(3, 100)  # Preço
        self._table.setColumnWidth(4, 60)   # Ativo

        layout = QVBoxLayout(self)
        layout.addLayout(top_bar)
        layout.addWidget(self._table)
        self.setLayout(layout)

        self._btn_edit.clicked.connect(self._on_edit_clicked)
        self._btn_refresh.clicked.connect(self.reload)
        self._btn_toggle_active.clicked.connect(self._on_toggle_active)
        self._btn_add.clicked.connect(self._on_add)
        self._show_inactive.stateChanged.connect(self.reload)

        # Atalhos (evitar conflito com Ctrl+N global)
        QShortcut(QKeySequence("F5"), self, self.reload)
        QShortcut(QKeySequence("F2"), self, self._on_edit_clicked)
        QShortcut(QKeySequence("Ctrl+T"), self, self._on_toggle_active)
        QShortcut(QKeySequence("Ctrl+Shift+N"), self, self._on_add)
        QShortcut(QKeySequence("Ctrl+I"), self, lambda: self._show_inactive.setChecked(not self._show_inactive.isChecked()))

        self.reload()

    def reload(self) -> None:
        services = self._controller.list_services(include_inactive=self._show_inactive.isChecked())
        self._populate(services)

    def _populate(self, services: List[Service]) -> None:
        self._table.setRowCount(len(services))
        for row, svc in enumerate(services):
            self._table.setItem(row, 0, QTableWidgetItem(svc.name))
            self._table.setItem(row, 1, QTableWidgetItem(svc.type))
            self._table.setItem(row, 2, QTableWidgetItem(svc.subtype or "-"))
            self._table.setItem(row, 3, QTableWidgetItem(self._format_brl(svc.price_cents)))
            self._table.setItem(row, 4, QTableWidgetItem("Sim" if svc.active else "Não"))
            self._table.setRowHeight(row, UI_TABLE_ROW_HEIGHT)
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, svc)
        self._table.resizeColumnsToContents()

    def _selected_service(self) -> Optional[Service]:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        item = self._table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole)

    def _on_edit_clicked(self) -> None:
        svc = self._selected_service()
        if not svc:
            QMessageBox.information(self, "Edição", "Selecione um serviço na tabela.")
            return
        dlg = ServiceEditorDialog(self, svc)
        if dlg.exec() == dlg.DialogCode.Accepted:
            new_price = dlg.new_price_cents()
            self._controller.update_price(svc, new_price)
            self.reload()

    def _on_toggle_active(self) -> None:
        svc = self._selected_service()
        if not svc:
            return
        self._controller.set_active(svc.id, not svc.active)
        self.reload()

    def _on_add(self) -> None:
        dlg = ServiceNewDialog(self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        name, type_, subtype, price_cents = dlg.values()
        self._controller.upsert(name, type_, subtype, price_cents, active=True)
        self.reload()

    @staticmethod
    def _format_brl(price_cents: int) -> str:
        value = price_cents / 100.0
        s = f"{value:,.2f}"
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {s}"
