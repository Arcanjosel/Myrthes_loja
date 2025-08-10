from __future__ import annotations

from typing import List, Optional

from app.models.order import OrderItem
from app.utils.firebase_repository import FirebaseRepository


class OrdersController:
    def __init__(self, repository: FirebaseRepository) -> None:
        self._repository = repository

    def create_order(self, client_id: str, items: List[OrderItem], due_date_iso: Optional[str] = None):
        order = self._repository.create_order(client_id, items, due_date_iso=due_date_iso)
        # Exemplo de baixa simples de estoque: zíper consome 1 unidade por item
        for it in items:
            if it.service_type == "troca_ziper":
                self._repository.adjust_inventory("ziper_padrao", -it.quantity)
        return order

    def update_status(self, order_id: str, status: str, delivered_at_iso: Optional[str]) -> None:
        self._repository.update_order_status(order_id, status, delivered_at_iso)

    def list_orders(self, status: Optional[str] = None, client_query: Optional[str] = None, order_code_query: Optional[str] = None):
        return self._repository.list_orders(status, client_query, order_code_query)

    def get_order_with_items(self, order_id: str):
        return self._repository.get_order_with_items(order_id)
