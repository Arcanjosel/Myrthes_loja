from __future__ import annotations

import json
import socket
import threading
import time
from typing import Optional

from app.data.sqlite import delete_sync_item, read_sync_batch


def is_online(timeout_seconds: float = 2.0) -> bool:
    try:
        socket.setdefaulttimeout(timeout_seconds)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except Exception:
        return False


class SyncManager:
    def __init__(self, firestore_client) -> None:
        self._db = firestore_client
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, name="SyncManager", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3)

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            # Modo offline: não envia nada para a nuvem
            if False:
                try:
                    self._flush_once()
                except Exception:
                    pass
            time.sleep(5)

    def _flush_once(self) -> None:
        batch = read_sync_batch(50)
        if not batch:
            return
        for item_id, entity, action, payload in batch:
            ok = self._apply_remote(entity, action, payload)
            if ok:
                delete_sync_item(item_id)

    # API pública para forçar flush manual (usada no diálogo de sincronização)
    def flush_now(self) -> int:
        """Força envio imediato da fila. Retorna quantos itens foram enviados com sucesso."""
        sent = 0
        batch = read_sync_batch(500)
        if not batch:
            return 0
        for item_id, entity, action, payload in batch:
            ok = self._apply_remote(entity, action, payload)
            if ok:
                delete_sync_item(item_id)
                sent += 1
        return sent

    def _apply_remote(self, entity: str, action: str, payload: str) -> bool:
        try:
            data = json.loads(payload)
            if entity == "service":
                col = self._db.collection("services")
                if action in ("upsert", "update_price"):
                    doc_id = data.get("id")
                    body = {k: v for k, v in data.items() if k != "id"}
                    if doc_id and str(doc_id).startswith("local:"):
                        col.add(body)
                    else:
                        if not doc_id:
                            col.add(body)
                        else:
                            col.document(doc_id).set(body, merge=True)
                elif action == "set_active":
                    doc_id = data.get("id")
                    col.document(doc_id).update({"active": bool(data.get("active", True))})
                return True
            if entity == "client":
                col = self._db.collection("clients")
                doc_id = data.get("id")
                body = {k: v for k, v in data.items() if k != "id"}
                if doc_id and str(doc_id).startswith("local:"):
                    col.add(body)
                else:
                    if not doc_id:
                        col.add(body)
                    else:
                        col.document(doc_id).set(body, merge=True)
                return True
            if entity == "order":
                col = self._db.collection("orders")
                if action == "upsert":
                    doc_id = data.get("id")
                    body = {k: v for k, v in data.items() if k != "id"}
                    if doc_id and str(doc_id).startswith("local:"):
                        col.add(body)
                    else:
                        if not doc_id:
                            col.add(body)
                        else:
                            col.document(doc_id).set(body, merge=True)
                elif action == "update_status":
                    doc_id = data["id"]
                    col.document(doc_id).update({
                        "status": data.get("status"),
                        "delivered_at_iso": data.get("delivered_at_iso")
                    })
                return True
            if entity == "inventory":
                col = self._db.collection("inventory")
                if action == "upsert":
                    doc_id = data.get("id")
                    body = {k: v for k, v in data.items() if k != "id"}
                    if not doc_id:
                        return True
                    col.document(doc_id).set(body, merge=True)
                elif action == "adjust":
                    doc_id = data.get("id")
                    if not doc_id:
                        return True
                    col.document(doc_id).set({"quantity": data.get("delta")}, merge=True)
                return True
            return True
        except Exception:
            return False
