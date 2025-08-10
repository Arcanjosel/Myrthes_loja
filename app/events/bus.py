from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal


class EventBus(QObject):
    client_list_changed = pyqtSignal()


bus = EventBus()
