from __future__ import annotations

from typing import List

from app.models.client import Client
from app.utils.firebase_repository import FirebaseRepository


class ClientController:
    def __init__(self, repository: FirebaseRepository) -> None:
        self._repository = repository

    def upsert(self, name: str, phone: str | None, notes: str | None) -> Client:
        client = Client(id=None, name=name.strip(), phone=(phone or '').strip() or None, notes=(notes or '').strip() or None)
        return self._repository.upsert_client(client)

    def list(self) -> List[Client]:
        return self._repository.list_clients()

    def search(self, query: str) -> List[Client]:
        return self._repository.search_clients(query)
