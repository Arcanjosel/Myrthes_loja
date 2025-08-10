from __future__ import annotations

from typing import List

from app.models.service import Service
from app.utils.firebase_repository import FirebaseRepository


class ServiceController:
    def __init__(self, repository: FirebaseRepository) -> None:
        self._repository = repository

    def list_services(self, include_inactive: bool = False) -> List[Service]:
        return self._repository.list_services(include_inactive=include_inactive)

    def update_price(self, service: Service, new_price_cents: int) -> None:
        self._repository.update_service_price(service, int(new_price_cents))

    def upsert(self, name: str, type_: str, subtype: str | None, price_cents: int, active: bool = True) -> Service:
        svc = Service(id=None, name=name.strip(), type=type_.strip(), subtype=(subtype or '').strip() or None, price_cents=int(price_cents), active=bool(active))
        return self._repository.upsert_service(svc)

    def set_active(self, service_id: str, active: bool) -> None:
        self._repository.set_service_active(service_id, active)
