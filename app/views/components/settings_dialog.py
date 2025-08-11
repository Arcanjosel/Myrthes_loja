from __future__ import annotations

from typing import Dict, Any, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from app.config import settings as app_settings
from app.views.components.dialog_theme import apply_dialog_theme, DialogHeader


class SettingsDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Configurações")
        self.setModal(True)
        self.resize(560, 520)

        self._fields: Dict[str, Any] = {}

        layout = QVBoxLayout(self)
        layout.addWidget(DialogHeader("Configurações", "Ajuste dados da empresa, impressora e aparência do sistema."))
        self._tabs = QTabWidget(self)
        layout.addWidget(self._tabs)

        self._build_company_tab()
        self._build_printer_tab()
        self._build_ui_tab()

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self._on_save)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

        self._load_values(app_settings.get_settings())
        apply_dialog_theme(self, min_width=560)

    # ----- Tabs -----
    def _build_company_tab(self) -> None:
        tab = QWidget(self)
        form = QFormLayout(tab)
        self._fields["APP_NAME"] = QLineEdit()
        self._fields["COMPANY_NAME"] = QLineEdit()
        self._fields["CNPJ"] = QLineEdit()
        self._fields["STATE_REGISTRATION_SP"] = QLineEdit()
        self._fields["PHONE"] = QLineEdit()

        form.addRow("Nome do App:", self._fields["APP_NAME"]) 
        form.addRow("Empresa:", self._fields["COMPANY_NAME"]) 
        form.addRow("CNPJ:", self._fields["CNPJ"]) 
        form.addRow("IE (SP):", self._fields["STATE_REGISTRATION_SP"]) 
        form.addRow("Telefone:", self._fields["PHONE"]) 

        tab.setLayout(form)
        self._tabs.addTab(tab, "Empresa")

    def _build_printer_tab(self) -> None:
        tab = QWidget(self)
        form = QFormLayout(tab)

        self._fields["THERMAL_PRINTER_VENDOR_ID"] = QLineEdit()
        self._fields["THERMAL_PRINTER_PRODUCT_ID"] = QLineEdit()
        self._fields["THERMAL_PRINTER_SERIAL_PORT"] = QLineEdit()
        self._fields["THERMAL_PRINTER_BAUDRATE"] = QSpinBox()
        self._fields["THERMAL_PRINTER_BAUDRATE"].setRange(1200, 256000)
        self._fields["THERMAL_PRINTER_HOST"] = QLineEdit()

        form.addRow("USB Vendor ID (ex 0x04b8):", self._fields["THERMAL_PRINTER_VENDOR_ID"]) 
        form.addRow("USB Product ID (ex 0x0e15):", self._fields["THERMAL_PRINTER_PRODUCT_ID"]) 
        form.addRow("Serial (COMx):", self._fields["THERMAL_PRINTER_SERIAL_PORT"]) 
        form.addRow("Baudrate:", self._fields["THERMAL_PRINTER_BAUDRATE"]) 
        form.addRow("Host (IP):", self._fields["THERMAL_PRINTER_HOST"]) 

        tab.setLayout(form)
        self._tabs.addTab(tab, "Impressora")

    def _build_ui_tab(self) -> None:
        tab = QWidget(self)
        form = QFormLayout(tab)

        self._fields["UI_FONT_FAMILY"] = QLineEdit()
        self._fields["UI_FONT_SIZE_PT"] = QSpinBox()
        self._fields["UI_FONT_SIZE_PT"].setRange(8, 32)
        self._fields["UI_TABLE_ROW_HEIGHT"] = QSpinBox()
        self._fields["UI_TABLE_ROW_HEIGHT"].setRange(16, 64)
        self._fields["UI_HEADER_FONT_DELTA"] = QSpinBox()
        self._fields["UI_HEADER_FONT_DELTA"].setRange(-4, 8)

        form.addRow("Fonte:", self._fields["UI_FONT_FAMILY"]) 
        form.addRow("Tamanho da Fonte:", self._fields["UI_FONT_SIZE_PT"]) 
        form.addRow("Altura da Linha:", self._fields["UI_TABLE_ROW_HEIGHT"]) 
        form.addRow("Delta do Cabeçalho:", self._fields["UI_HEADER_FONT_DELTA"]) 

        tab.setLayout(form)
        self._tabs.addTab(tab, "Aparência")

    # ----- Data binding -----
    def _load_values(self, values: Dict[str, Any]) -> None:
        def set_line(key: str, widget: QLineEdit) -> None:
            widget.setText("" if values.get(key) is None else str(values.get(key)))

        for key in (
            "APP_NAME",
            "COMPANY_NAME",
            "CNPJ",
            "STATE_REGISTRATION_SP",
            "PHONE",
            "THERMAL_PRINTER_VENDOR_ID",
            "THERMAL_PRINTER_PRODUCT_ID",
            "THERMAL_PRINTER_SERIAL_PORT",
            "THERMAL_PRINTER_HOST",
            "UI_FONT_FAMILY",
        ):
            w = self._fields.get(key)
            if isinstance(w, QLineEdit):
                set_line(key, w)

        spinners = {
            "THERMAL_PRINTER_BAUDRATE": int(values.get("THERMAL_PRINTER_BAUDRATE", 9600)),
            "UI_FONT_SIZE_PT": int(values.get("UI_FONT_SIZE_PT", 12)),
            "UI_TABLE_ROW_HEIGHT": int(values.get("UI_TABLE_ROW_HEIGHT", 28)),
            "UI_HEADER_FONT_DELTA": int(values.get("UI_HEADER_FONT_DELTA", 1)),
        }
        for key, val in spinners.items():
            w = self._fields.get(key)
            if isinstance(w, QSpinBox):
                w.setValue(val)

    def _collect_values(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for key, w in self._fields.items():
            if isinstance(w, QLineEdit):
                text = w.text().strip()
                data[key] = text if text != "" else None
            elif isinstance(w, QSpinBox):
                data[key] = int(w.value())
        return data

    def _on_save(self) -> None:
        try:
            values = self._collect_values()
            app_settings.save_settings(values)
            QMessageBox.information(self, "Configurações", "Configurações salvas com sucesso.")
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar configurações: {exc}")


