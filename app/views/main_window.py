from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QLabel, QMainWindow, QStatusBar, QTabWidget, QWidget, QVBoxLayout

from app.config.settings import WINDOW_TITLE, APP_NAME, PHONE, CNPJ
from app.controllers.service_controller import ServiceController
from app.controllers.client_controller import ClientController
from app.controllers.orders_controller import OrdersController
from app.utils.firebase_repository import FirebaseRepository
from app.views.clients_view import ClientsView
from app.views.services_view import ServicesView
from app.views.orders_list_view import OrdersListView
from app.utils.icons_manager import IconManager
from app.views.components.settings_dialog import SettingsDialog
from app.views.components.sync_dialog import SyncDialog
from app.views.components.header_bar import HeaderBar


class MainWindow(QMainWindow):
    def __init__(
        self,
        repository: FirebaseRepository,
        service_controller: ServiceController,
    ) -> None:
        super().__init__()
        self._repository = repository
        self._service_controller = service_controller
        self._client_controller = ClientController(repository)
        self._orders_controller = OrdersController(repository)

        self.setWindowTitle(WINDOW_TITLE)
        self.resize(1100, 760)

        self._tabs = QTabWidget(self)
        self._tab_clients = ClientsView(self._client_controller)
        self._tab_services = ServicesView(self._service_controller)
        self._tab_orders_list = OrdersListView(
            self._orders_controller, self._client_controller, self._service_controller
        )

        self._tabs.addTab(self._tab_orders_list, "Pedidos")
        self._tabs.addTab(self._tab_clients, "Clientes")
        self._tabs.addTab(self._tab_services, "Serviços")

        # Header com logo + ações
        header_actions = [
            ("pedido", "Novo Pedido", "Ctrl+N", lambda: self._tab_orders_list.open_new_order()),
            ("clientes", "Clientes", "Ctrl+Shift+C", lambda: self._tabs.setCurrentWidget(self._tab_clients)),
            ("servicos", "Serviços", "Ctrl+Shift+S", lambda: self._tabs.setCurrentWidget(self._tab_services)),
            ("config", "Configurações", "Ctrl+,", self._open_settings_dialog),
        ]
        header = HeaderBar(WINDOW_TITLE, header_actions, self)
        header.setObjectName("HeaderBar")

        # Container central: header acima das abas
        central = QWidget(self)
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(header)
        vbox.addWidget(self._tabs)
        self.setCentralWidget(central)

        self._build_status_bar()
        self._build_menu()

    def _build_status_bar(self) -> None:
        sb = QStatusBar(self)
        self._sync_label = QLabel("Sincronização: 0 pendências")
        status = f"{APP_NAME} | Tel: {PHONE} | CNPJ: {CNPJ}"
        label = QLabel(status)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        sb.addWidget(label)
        sb.addPermanentWidget(self._sync_label)
        self.setStatusBar(sb)

        timer = QTimer(self)
        timer.timeout.connect(self._update_sync_count)
        timer.start(5000)
        self._update_sync_count()

    def _update_sync_count(self) -> None:
        try:
            n = self._repository.count_sync_queue()
            self._sync_label.setText(f"Sincronização: {n} pendências")
        except Exception:
            self._sync_label.setText("Sincronização: -")

    def _build_menu(self) -> None:
        menu_file = self.menuBar().addMenu("Arquivo")
        act_quit = QAction(IconManager.get_icon("sair"), "Sair", self)
        act_quit.setShortcut(QKeySequence("Ctrl+Q"))
        act_quit.triggered.connect(self.close)
        menu_file.addAction(act_quit)

        menu_nav = self.menuBar().addMenu("Atalhos")
        act_new_order = QAction(IconManager.get_icon("pedido"), "Novo Pedido", self)
        act_new_order.setShortcut(QKeySequence("Ctrl+N"))
        act_new_order.triggered.connect(lambda: self._tab_orders_list.open_new_order())
        menu_nav.addAction(act_new_order)

        act_list_orders = QAction(IconManager.get_icon("lista"), "Lista de Pedidos", self)
        act_list_orders.setShortcut(QKeySequence("Ctrl+L"))
        act_list_orders.triggered.connect(lambda: self._tabs.setCurrentWidget(self._tab_orders_list))
        menu_nav.addAction(act_list_orders)

        act_clients = QAction(IconManager.get_icon("clientes"), "Clientes", self)
        act_clients.setShortcut(QKeySequence("Ctrl+Shift+C"))
        act_clients.triggered.connect(lambda: self._tabs.setCurrentWidget(self._tab_clients))
        menu_nav.addAction(act_clients)

        act_services = QAction(IconManager.get_icon("servicos"), "Serviços", self)
        act_services.setShortcut(QKeySequence("Ctrl+Shift+S"))
        act_services.triggered.connect(lambda: self._tabs.setCurrentWidget(self._tab_services))
        menu_nav.addAction(act_services)

        # Configurações
        menu_settings = self.menuBar().addMenu("Configurações")
        act_settings = QAction(IconManager.get_icon("config"), "Abrir Configurações", self)
        act_settings.setShortcut(QKeySequence("Ctrl+,"))
        act_settings.triggered.connect(self._open_settings_dialog)
        menu_settings.addAction(act_settings)
        act_sync = QAction(IconManager.get_icon("refresh"), "Sincronizar agora…", self)
        act_sync.setShortcut(QKeySequence("Ctrl+Shift+R"))
        act_sync.triggered.connect(self._open_sync_dialog)
        menu_settings.addAction(act_sync)

    def _open_settings_dialog(self) -> None:
        dlg = SettingsDialog(self)
        if dlg.exec():
            # Recarrega título após salvar
            from app.config.settings import WINDOW_TITLE
            self.setWindowTitle(WINDOW_TITLE)

    def _open_sync_dialog(self) -> None:
        from app.config import firebase_config
        from app.utils.sync_manager import SyncManager

        # Reusa o SyncManager já em execução, se existir
        # self._sync_manager é criado em main.py, então garantimos atributo
        sync_mgr = getattr(self, "_sync_manager", None)
        if not isinstance(sync_mgr, SyncManager):
            sync_mgr = None
        dlg = SyncDialog(self, sync_mgr or SyncManager(firebase_config.get_firestore_client()))
        dlg.exec()
