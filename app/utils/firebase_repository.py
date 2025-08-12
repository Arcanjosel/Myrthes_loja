from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import uuid4

from app.data import sqlite as sqldb
from app.models.client import Client
from app.models.order import Order, OrderItem
from app.models.service import Service


class FirebaseRepository:
    """Acesso ao Firestore com persistência offline (SQLite) e fila de sincronização.
    """

    def __init__(self, firestore_client) -> None:
        # Cliente Firestore é ignorado em modo offline
        self._db = None
        sqldb.init_db()

    # --------- Serviços ---------
    def ensure_default_services(self) -> None:
        defaults = [
            Service(None, "Ajuste de tamanho", "ajuste_tamanho", None, 4500),
            Service(None, "Troca de zíper", "troca_ziper", None, 5500),
            Service(None, "Barra", "barra", "Original", 3500),
            Service(None, "Barra", "barra", "Simples", 2500),
            Service(None, "Pence", "pence", None, 3000),
        ]
        if not sqldb.list_services():
            for svc in defaults:
                local = Service(
                    id=f"local:{svc.name}:{svc.type}:{svc.subtype or ''}",
                    name=svc.name,
                    type=svc.type,
                    subtype=svc.subtype,
                    price_cents=svc.price_cents,
                    active=True,
                )
                sqldb.upsert_service(local)

    def list_services(self, include_inactive: bool = False) -> List[Service]:
        return sqldb.list_services(include_inactive=include_inactive)

    def upsert_service(self, service: Service) -> Service:
        if not service.id:
            service.id = f"local:{service.name}:{service.type}:{service.subtype or ''}"
        sqldb.upsert_service(service)
        sqldb.enqueue_sync("service", "upsert", json.dumps(service.__dict__))
        return service

    def set_service_active(self, service_id: str, active: bool) -> None:
        sqldb.set_service_active(service_id, active)
        sqldb.enqueue_sync("service", "set_active", json.dumps({"id": service_id, "active": bool(active)}))

    def update_service_price(self, target: Service, new_price_cents: int) -> None:
        target.price_cents = int(new_price_cents)
        sqldb.update_service_price(target, target.price_cents)
        payload = {
            "id": target.id,
            "price_cents": target.price_cents,
            "name": target.name,
            "type": target.type,
            "subtype": target.subtype,
            "active": target.active,
        }
        action = "update_price" if target.id and not str(target.id).startswith("local:") else "upsert"
        sqldb.enqueue_sync("service", action, json.dumps(payload))

    # --------- Clientes ---------
    def upsert_client(self, client: Client) -> Client:
        saved = sqldb.upsert_client(client)
        sqldb.enqueue_sync("client", "upsert", json.dumps(saved.__dict__))
        return saved

    def list_clients(self) -> List[Client]:
        return sqldb.list_clients()

    def search_clients(self, query: str) -> List[Client]:
        query = (query or "").strip()
        return sqldb.search_clients(query) if query else self.list_clients()

    # --------- Pedidos ---------
    def create_order(self, client_id: str, items: List[OrderItem], due_date_iso: Optional[str] = None) -> Order:
        created_at_iso = datetime.now(timezone.utc).isoformat()
        total = sum(i.unit_price_cents * i.quantity for i in items)
        order_code = f"MC-{datetime.now().strftime('%y%m%d')}-{str(uuid4())[:8]}"
        order = Order(
            id=None,
            client_id=client_id,
            created_at_iso=created_at_iso,
            total_cents=total,
            items=items,
            due_date_iso=due_date_iso,
            order_code=order_code,
        )
        saved = sqldb.create_order(order)
        payload = {
            "id": saved.id,
            "client_id": saved.client_id,
            "created_at_iso": saved.created_at_iso,
            "status": saved.status,
            "total_cents": saved.total_cents,
            "due_date_iso": saved.due_date_iso,
            "delivered_at_iso": saved.delivered_at_iso,
            "order_code": saved.order_code,
            "items": [
                {
                    "service_name": it.service_name,
                    "service_type": it.service_type,
                    "service_subtype": it.service_subtype,
                    "unit_price_cents": it.unit_price_cents,
                    "quantity": it.quantity,
                }
                for it in items
            ],
        }
        sqldb.enqueue_sync("order", "upsert", json.dumps(payload))
        return saved

    # --------- Pagamentos / Caixa ---------
    def add_payment(self, order_id: str, amount_cents: int, method: str | None = None, note: str | None = None) -> None:
        sqldb.add_payment(order_id, int(amount_cents), method, note)

    def cash_sum_for_date(self, date_iso: str) -> int:
        return sqldb.cash_sum_for_date(date_iso)

    def update_order_status(self, order_id: str, status: str, delivered_at_iso: Optional[str]) -> None:
        sqldb.update_order_status(order_id, status, delivered_at_iso)
        payload = {"id": order_id, "status": status, "delivered_at_iso": delivered_at_iso}
        sqldb.enqueue_sync("order", "update_status", json.dumps(payload))

    def list_orders(self, status: Optional[str] = None, client_query: Optional[str] = None, order_code_query: Optional[str] = None):
        return sqldb.list_orders(status, client_query, order_code_query)

    def get_order_with_items(self, order_id: str):
        return sqldb.get_order_with_items(order_id)

    def delete_order(self, order_id: str) -> None:
        # Remove local e deixa uma marca de remoção opcionalmente no remoto (não implementado)
        sqldb.delete_order(order_id)

    # --------- Estoque ---------
    def list_inventory(self) -> List[Tuple[str, str, str, int]]:
        return sqldb.list_inventory()

    def upsert_inventory_item(self, item_id: str, name: str, unit: str, quantity: int) -> None:
        sqldb.upsert_inventory_item(item_id, name, unit, quantity)
        payload = {"id": item_id, "name": name, "unit": unit, "quantity": int(quantity)}
        sqldb.enqueue_sync("inventory", "upsert", json.dumps(payload))

    def adjust_inventory(self, item_id: str, delta: int) -> None:
        sqldb.adjust_inventory(item_id, delta)
        payload = {"id": item_id, "delta": int(delta)}
        sqldb.enqueue_sync("inventory", "adjust", json.dumps(payload))

    # --------- Sync ---------
    def count_sync_queue(self) -> int:
        return sqldb.count_sync_queue()

    # --------- Analytics ---------
    def top_services_by_revenue(self, limit: int = 10, last_n_days: int | None = None):
        return sqldb.top_services_by_revenue(limit, last_n_days)

    def bottom_services_by_revenue(self, limit: int = 10, last_n_days: int | None = None):
        return sqldb.bottom_services_by_revenue(limit, last_n_days)

    def revenue_by_day(self, last_n_days: int = 30):
        return sqldb.revenue_by_day(last_n_days)

    def summary_since(self, last_n_days: int = 30):
        return sqldb.summary_since(last_n_days)
