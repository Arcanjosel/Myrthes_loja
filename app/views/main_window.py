from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QLabel, QMainWindow, QStatusBar, QTabWidget, QToolBar

from app.config.settings import WINDOW_TITLE, APP_NAME, PHONE, CNPJ
from app.controllers.service_controller import ServiceController
from app.controllers.client_controller import ClientController
from app.controllers.orders_controller import OrdersController
from app.utils.firebase_repository import FirebaseRepository
from app.views.clients_view import ClientsView
from app.views.inventory_view import InventoryView
from app.views.orders_view import OrdersView
from app.views.services_view import ServicesView
from app.views.orders_list_view import OrdersListView


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
        self._tab_services = ServicesView(service_controller)
        self._tab_clients = ClientsView(self._client_controller)
        self._tab_orders = OrdersView(self._client_controller, self._service_controller, self._orders_controller)
        self._tab_orders_list = OrdersListView(self._orders_controller)
        self._tab_inventory = InventoryView(self._repository)

        self._tabs.addTab(self._tab_orders, "Novo Pedido")
        self._tabs.addTab(self._tab_orders_list, "Pedidos")
        self._tabs.addTab(self._tab_clients, "Clientes")
        self._tabs.addTab(self._tab_services, "Serviços")
        self._tabs.addTab(self._tab_inventory, "Estoque")

        self.setCentralWidget(self._tabs)

        self._build_toolbar()
        self._build_status_bar()
        self._build_menu()

    def _build_toolbar(self) -> None:
        tb = QToolBar("Ações")
        self.addToolBar(tb)
        act_new_order = QAction("Novo Pedido", self)
        act_list_orders = QAction("Lista Pedidos", self)
        act_clients = QAction("Clientes", self)
        act_services = QAction("Serviços", self)
        act_inventory = QAction("Estoque", self)
        act_new_order.triggered.connect(lambda: self._tabs.setCurrentWidget(self._tab_orders))
        act_list_orders.triggered.connect(lambda: self._tabs.setCurrentWidget(self._tab_orders_list))
        act_clients.triggered.connect(lambda: self._tabs.setCurrentWidget(self._tab_clients))
        act_services.triggered.connect(lambda: self._tabs.setCurrentWidget(self._tab_services))
        act_inventory.triggered.connect(lambda: self._tabs.setCurrentWidget(self._tab_inventory))
        for act in [act_new_order, act_list_orders, act_clients, act_services, act_inventory]:
            tb.addAction(act)

    def _build_status_bar(self) -> None:
        sb = QStatusBar(self)
        self._sync_label = QLabel("Sincronização: 0 pendências")
        status = f"{APP_NAME} | Tel: {PHONE} | CNPJ: {CNPJ}"
        label = QLabel(status)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        sb.addWidget(label)
        sb.addPermanentWidget(self._sync_label)
        self.setStatusBar(sb)

        # Atualiza contagem da fila a cada 5s
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
        menu = self.menuBar().addMenu("Arquivo")
        act_quit = QAction("Sair", self)
        act_quit.triggered.connect(self.close)
        menu.addAction(act_quit)
