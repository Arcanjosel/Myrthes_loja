from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QCheckBox,
    QLineEdit,
    QLabel,
    QSpinBox,
    QComboBox,
    QGroupBox,
)

from app.controllers.service_controller import ServiceController
from app.models.service import Service
from app.views.components.service_editor_dialog import ServiceEditorDialog


class ServicesView(QWidget):
    def __init__(self, controller: ServiceController):
        super().__init__()
        self._controller = controller

        # Filtros e ações
        self._show_inactive = QCheckBox("Mostrar inativos")
        self._btn_refresh = QPushButton("Atualizar")
        self._btn_edit = QPushButton("Editar preço")
        self._btn_toggle_active = QPushButton("Ativar/Desativar")

        # Tabela
        self._table = QTableWidget(self)
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Serviço", "Tipo", "Subtipo", "Preço", "Ativo"])
        self._table.setSelectionBehavior(self._table.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)

        # Formulário de novo serviço
        form_box = QGroupBox("Novo serviço")
        self._name = QLineEdit()
        self._type = QComboBox()
        self._type.setEditable(True)
        self._type.addItems(["ajuste_tamanho", "troca_ziper", "barra", "pence"])  # base inicial
        self._subtype = QLineEdit()
        self._price = QSpinBox()
        self._price.setRange(0, 1_000_000)
        self._price.setSingleStep(100)
        self._price.setSuffix(" centavos")
        self._btn_add = QPushButton("Adicionar")

        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Nome:"))
        form_layout.addWidget(self._name)
        form_layout.addWidget(QLabel("Tipo:"))
        form_layout.addWidget(self._type)
        form_layout.addWidget(QLabel("Subtipo:"))
        form_layout.addWidget(self._subtype)
        form_layout.addWidget(QLabel("Preço:"))
        form_layout.addWidget(self._price)
        form_layout.addWidget(self._btn_add)
        form_box.setLayout(form_layout)

        # Barras
        top_bar = QHBoxLayout()
        top_bar.addWidget(self._show_inactive)
        top_bar.addWidget(self._btn_refresh)
        top_bar.addWidget(self._btn_edit)
        top_bar.addWidget(self._btn_toggle_active)
        top_bar.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(top_bar)
        layout.addWidget(self._table)
        layout.addWidget(form_box)
        self.setLayout(layout)

        self._btn_edit.clicked.connect(self._on_edit_clicked)
        self._btn_refresh.clicked.connect(self.reload)
        self._btn_toggle_active.clicked.connect(self._on_toggle_active)
        self._btn_add.clicked.connect(self._on_add)
        self._show_inactive.stateChanged.connect(self.reload)

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
            self._table.setRowHeight(row, 24)
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
        name = self._name.text().strip()
        if not name:
            return
        type_ = self._type.currentText().strip()
        subtype = self._subtype.text().strip() or None
        price_cents = int(self._price.value())
        self._controller.upsert(name, type_, subtype, price_cents, active=True)
        self._name.clear()
        self._subtype.clear()
        self._price.setValue(0)
        self.reload()

    @staticmethod
    def _format_brl(price_cents: int) -> str:
        value = price_cents / 100.0
        s = f"{value:,.2f}"
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {s}"
