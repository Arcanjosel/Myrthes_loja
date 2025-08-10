APP_NAME = "Myrthes Costuras"
COMPANY_NAME = "Mirtes Eliane Oliveira Costa"
CNPJ = "42.275.758/0001-82"
STATE_REGISTRATION_SP = "797.744.619.116"
PHONE = "(16) 98854-7350"

WINDOW_TITLE = f"{APP_NAME} — Gestão de Oficina"

# Persistência offline (SQLite)
DB_PATH = "myrthes.db"

# Impressora térmica (opções):
# - USB: defina VENDOR_ID e PRODUCT_ID
# - Serial: defina SERIAL_PORT (ex.: 'COM3') e BAUDRATE
# - Network: defina PRINTER_HOST (ex.: '192.168.0.50')
THERMAL_PRINTER_VENDOR_ID = None  # ex.: 0x04b8
THERMAL_PRINTER_PRODUCT_ID = None  # ex.: 0x0e15
THERMAL_PRINTER_SERIAL_PORT = None  # ex.: 'COM3'
THERMAL_PRINTER_BAUDRATE = 9600
THERMAL_PRINTER_HOST = None
