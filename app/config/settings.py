from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

# -------- Defaults --------
_DEFAULTS: Dict[str, Any] = {
    "APP_NAME": "Myrthes Costuras",
    "COMPANY_NAME": "Mirtes Eliane Oliveira Costa",
    "CNPJ": "42.275.758/0001-82",
    "STATE_REGISTRATION_SP": "797.744.619.116",
    "PHONE": "(16) 98854-7350",
    # Persistência offline (SQLite)
    "DB_PATH": "myrthes.db",
    # Impressora térmica
    "THERMAL_PRINTER_VENDOR_ID": None,  # ex.: 0x04b8
    "THERMAL_PRINTER_PRODUCT_ID": None,  # ex.: 0x0e15
    "THERMAL_PRINTER_SERIAL_PORT": None,  # ex.: 'COM3'
    "THERMAL_PRINTER_BAUDRATE": 9600,
    "THERMAL_PRINTER_HOST": None,
    # Aparência (UI)
    "UI_FONT_FAMILY": "Segoe UI",
    "UI_FONT_SIZE_PT": 12,
    "UI_TABLE_ROW_HEIGHT": 28,
    "UI_HEADER_FONT_DELTA": 1,
    "UI_THEME": "system",  # system | dark
    # Sincronização / Credenciais Firebase (opcional override)
    "FIREBASE_CREDENTIALS": None,
}

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SETTINGS_FILE = _PROJECT_ROOT / "settings.json"

_CURRENT: Dict[str, Any] = _DEFAULTS.copy()


def _coerce_types(d: Dict[str, Any]) -> Dict[str, Any]:
    coerced = _DEFAULTS.copy()
    for key, default_value in _DEFAULTS.items():
        if key not in d:
            continue
        value = d[key]
        if key in {"THERMAL_PRINTER_VENDOR_ID", "THERMAL_PRINTER_PRODUCT_ID"}:
            # aceitar int ou string (hex/decimal)
            if value in ("", None):
                coerced[key] = None
            else:
                try:
                    if isinstance(value, str):
                        coerced[key] = int(value, 0)
                    else:
                        coerced[key] = int(value)
                except Exception:
                    coerced[key] = None
        else:
            coerced[key] = value
    return coerced


def load_settings() -> Dict[str, Any]:
    global _CURRENT
    if _SETTINGS_FILE.is_file():
        try:
            data = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
            _CURRENT.update(_coerce_types(data))
        except Exception:
            # se arquivo corrompido, mantém defaults
            pass
    _apply_runtime_overrides()
    return _CURRENT.copy()


def save_settings(values: Dict[str, Any]) -> None:
    global _CURRENT
    _CURRENT.update(_coerce_types(values))
    try:
        _SETTINGS_FILE.write_text(json.dumps(_CURRENT, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    _apply_runtime_overrides()


def get_settings() -> Dict[str, Any]:
    return _CURRENT.copy()


def _apply_runtime_overrides() -> None:
    # Exporta variáveis de módulo para retrocompatibilidade
    globals().update({k: _CURRENT.get(k, v) for k, v in _DEFAULTS.items()})
    globals()["WINDOW_TITLE"] = f"{_CURRENT.get('APP_NAME', _DEFAULTS['APP_NAME'])} — Gestão de Oficina"


# Carrega na importação do módulo
load_settings()
