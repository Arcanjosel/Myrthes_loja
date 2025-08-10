from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Client:
    id: Optional[str]
    name: str
    phone: Optional[str]
    notes: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "phone": self.phone,
            "notes": self.notes,
        }

    @staticmethod
    def from_doc(doc: Any) -> "Client":
        data = doc.to_dict() if hasattr(doc, "to_dict") else doc
        return Client(
            id=getattr(doc, "id", data.get("id")),
            name=data.get("name", ""),
            phone=data.get("phone"),
            notes=data.get("notes"),
        )
