import sys
from PyQt6.QtWidgets import QApplication

from app.config.firebase_config import get_firestore_client
from app.utils.firebase_repository import FirebaseRepository
from app.controllers.service_controller import ServiceController
from app.views.main_window import MainWindow
from app.utils.sync_manager import SyncManager


def main() -> int:
    app = QApplication(sys.argv)

    firestore_client = get_firestore_client()
    repository = FirebaseRepository(firestore_client)
    repository.ensure_default_services()

    sync = SyncManager(firestore_client)
    sync.start()
    # expõe para a janela poder abrir o diálogo de sync reutilizando a thread
    setattr(MainWindow, "_sync_manager", sync)

    service_controller = ServiceController(repository)

    window = MainWindow(
        repository=repository,
        service_controller=service_controller,
    )
    window.show()

    code = app.exec()
    sync.stop()
    return code


if __name__ == "__main__":
    sys.exit(main())
