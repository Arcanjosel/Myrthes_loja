from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class OrderItem:
    service_name: str
    service_type: str
    service_subtype: Optional[str]
    unit_price_cents: int
    quantity: int


@dataclass
class Order:
    id: Optional[str]
    client_id: str
    created_at_iso: str
    status: str = "aberto"
    total_cents: int = 0
    items: List[OrderItem] = field(default_factory=list)
    due_date_iso: Optional[str] = None
    delivered_at_iso: Optional[str] = None
    order_code: Optional[str] = None
