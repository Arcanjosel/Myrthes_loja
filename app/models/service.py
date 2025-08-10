from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Service:
    id: Optional[str]
    name: str
    type: str
    subtype: Optional[str]
    price_cents: int
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "subtype": self.subtype,
            "price_cents": self.price_cents,
            "active": self.active,
        }

    @staticmethod
    def from_doc(doc: Any) -> "Service":
        data = doc.to_dict() if hasattr(doc, "to_dict") else doc
        return Service(
            id=getattr(doc, "id", data.get("id")),
            name=data.get("name", ""),
            type=data.get("type", ""),
            subtype=data.get("subtype"),
            price_cents=int(data.get("price_cents", 0)),
            active=bool(data.get("active", True)),
        )
