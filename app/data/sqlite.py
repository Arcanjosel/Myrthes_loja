from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Generator, List, Optional, Tuple
from uuid import uuid4

from app.config.settings import DB_PATH
from app.models.client import Client
from app.models.order import Order, OrderItem
from app.models.service import Service


@contextmanager
def get_conn() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        # Serviços
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS services (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                subtype TEXT,
                price_cents INTEGER NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        # Clientes
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT,
                notes TEXT
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(name)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_clients_phone ON clients(phone)")
        # Pedidos
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                created_at_iso TEXT NOT NULL,
                status TEXT NOT NULL,
                total_cents INTEGER NOT NULL,
                due_date_iso TEXT,
                delivered_at_iso TEXT,
                order_code TEXT,
                FOREIGN KEY(client_id) REFERENCES clients(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                service_name TEXT NOT NULL,
                service_type TEXT NOT NULL,
                service_subtype TEXT,
                unit_price_cents INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(id)
            )
            """
        )
        # Fila de sync
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity TEXT NOT NULL,
                action TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Pagamentos (registro simples de entradas)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                amount_cents INTEGER NOT NULL,
                method TEXT,
                note TEXT,
                created_at_iso TEXT NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(id)
            )
            """
        )
        # Estoque básico
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                unit TEXT NOT NULL,
                quantity INTEGER NOT NULL
            )
            """
        )
        conn.commit()


# ---------- Serviços ----------

def upsert_service(service: Service) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO services (id, name, type, subtype, price_cents, active)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                type=excluded.type,
                subtype=excluded.subtype,
                price_cents=excluded.price_cents,
                active=excluded.active
            """,
            (
                service.id or f"local:{service.name}:{service.type}:{service.subtype or ''}",
                service.name,
                service.type,
                service.subtype,
                int(service.price_cents),
                1 if service.active else 0,
            ),
        )


def list_services(include_inactive: bool = False) -> List[Service]:
    with get_conn() as conn:
        if include_inactive:
            rows = conn.execute(
                "SELECT id, name, type, subtype, price_cents, active FROM services"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, name, type, subtype, price_cents, active FROM services WHERE active = 1"
            ).fetchall()
        return [
            Service(
                id=r[0],
                name=r[1],
                type=r[2],
                subtype=r[3],
                price_cents=int(r[4]),
                active=bool(r[5]),
            )
            for r in rows
        ]


def update_service_price(service: Service, new_price_cents: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE services SET price_cents = ? WHERE id = ?",
            (int(new_price_cents), service.id),
        )


def set_service_active(service_id: str, active: bool) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE services SET active = ? WHERE id = ?",
            (1 if active else 0, service_id),
        )


# ---------- Clientes ----------

def upsert_client(client: Client) -> Client:
    cid = client.id or f"local:client:{uuid4()}"
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO clients (id, name, phone, notes)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                phone=excluded.phone,
                notes=excluded.notes
            """,
            (cid, client.name, client.phone, client.notes),
        )
    return Client(id=cid, name=client.name, phone=client.phone, notes=client.notes)


def list_clients() -> List[Client]:
    with get_conn() as conn:
        rows = conn.execute("SELECT id, name, phone, notes FROM clients ORDER BY name ASC").fetchall()
        return [Client(id=r[0], name=r[1], phone=r[2], notes=r[3]) for r in rows]


def search_clients(query: str) -> List[Client]:
    like = f"%{query.strip()}%"
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, name, phone, notes FROM clients
            WHERE name LIKE ? OR phone LIKE ?
            ORDER BY name ASC
            """,
            (like, like),
        ).fetchall()
        return [Client(id=r[0], name=r[1], phone=r[2], notes=r[3]) for r in rows]


def get_client_by_id(client_id: str) -> Optional[Client]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, name, phone, notes FROM clients WHERE id = ?",
            (client_id,),
        ).fetchone()
    if not row:
        return None
    return Client(id=row[0], name=row[1], phone=row[2], notes=row[3])


# ---------- Pedidos ----------

def create_order(order: Order) -> Order:
    oid = order.id or f"local:order:{uuid4()}"
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO orders (id, client_id, created_at_iso, status, total_cents, due_date_iso, delivered_at_iso, order_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                oid,
                order.client_id,
                order.created_at_iso,
                order.status,
                int(order.total_cents),
                order.due_date_iso,
                order.delivered_at_iso,
                order.order_code,
            ),
        )
        for it in order.items:
            conn.execute(
                """
                INSERT INTO order_items (
                    order_id, service_name, service_type, service_subtype, unit_price_cents, quantity
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    oid,
                    it.service_name,
                    it.service_type,
                    it.service_subtype,
                    int(it.unit_price_cents),
                    int(it.quantity),
                ),
            )
    return Order(
        id=oid,
        client_id=order.client_id,
        created_at_iso=order.created_at_iso,
        status=order.status,
        total_cents=order.total_cents,
        items=order.items,
        due_date_iso=order.due_date_iso,
        delivered_at_iso=order.delivered_at_iso,
        order_code=order.order_code,
    )


def update_order_status(order_id: str, status: str, delivered_at_iso: Optional[str]) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE orders SET status = ?, delivered_at_iso = ? WHERE id = ?",
            (status, delivered_at_iso, order_id),
        )


def list_orders(status: Optional[str] = None, client_query: Optional[str] = None, order_code_query: Optional[str] = None) -> List[Tuple[str, str, str, str, int, Optional[str]]]:
    """Retorna lista de pedidos: (id, order_code, client_name, status, total_cents, due_date_iso)."""
    where = []
    params: List[object] = []
    if status and status != "todos":
        where.append("o.status = ?")
        params.append(status)
    if client_query:
        where.append("(c.name LIKE ? OR c.phone LIKE ?)")
        like = f"%{client_query}%"
        params.extend([like, like])
    if order_code_query:
        where.append("o.order_code LIKE ?")
        params.append(f"%{order_code_query}%")
    sql = (
        "SELECT o.id, o.order_code, COALESCE(c.name,''), o.status, o.total_cents, o.due_date_iso "
        "FROM orders o LEFT JOIN clients c ON c.id = o.client_id"
    )
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY o.created_at_iso DESC"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [(r[0], r[1], r[2], r[3], int(r[4]), r[5]) for r in rows]


def get_order_with_items(order_id: str) -> Optional[Tuple[Order, List[OrderItem]]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, client_id, created_at_iso, status, total_cents, due_date_iso, delivered_at_iso, order_code FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()
        if not row:
            return None
        items_rows = conn.execute(
            "SELECT service_name, service_type, service_subtype, unit_price_cents, quantity FROM order_items WHERE order_id = ?",
            (order_id,),
        ).fetchall()
    items = [
        OrderItem(
            service_name=ir[0],
            service_type=ir[1],
            service_subtype=ir[2],
            unit_price_cents=int(ir[3]),
            quantity=int(ir[4]),
        )
        for ir in items_rows
    ]
    order = Order(
        id=row[0],
        client_id=row[1],
        created_at_iso=row[2],
        status=row[3],
        total_cents=int(row[4]),
        due_date_iso=row[5],
        delivered_at_iso=row[6],
        order_code=row[7],
        items=items,
    )
    return order, items


# ---------- Fila de sincronização ----------

def enqueue_sync(entity: str, action: str, payload_json: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO sync_queue (entity, action, payload) VALUES (?, ?, ?)",
            (entity, action, payload_json),
        )


def read_sync_batch(limit: int = 50) -> List[Tuple[int, str, str, str]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, entity, action, payload FROM sync_queue ORDER BY id ASC LIMIT ?",
            (limit,),
        ).fetchall()
        return list(rows)


def delete_sync_item(item_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM sync_queue WHERE id = ?", (item_id,))


def count_sync_queue() -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(1) FROM sync_queue").fetchone()
        return int(row[0]) if row else 0


# ---------- Estoque ----------

def list_inventory() -> List[Tuple[str, str, str, int]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT id, name, unit, quantity FROM inventory ORDER BY name ASC").fetchall()
        return list(rows)


def upsert_inventory_item(item_id: str, name: str, unit: str, quantity: int) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO inventory (id, name, unit, quantity)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                unit=excluded.unit,
                quantity=excluded.quantity
            """,
            (item_id, name, unit, int(quantity)),
        )


def adjust_inventory(item_id: str, delta: int) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE inventory SET quantity = quantity + ? WHERE id = ?", (int(delta), item_id))


# ---------- Pagamentos / Caixa ----------

def add_payment(order_id: str, amount_cents: int, method: str | None = None, note: str | None = None, created_at_iso: str | None = None) -> None:
    """Registra uma entrada de pagamento para um pedido."""
    from datetime import datetime, timezone

    created = created_at_iso or datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO payments (order_id, amount_cents, method, note, created_at_iso)
            VALUES (?, ?, ?, ?, ?)
            """,
            (order_id, int(amount_cents), method, note, created),
        )


def cash_sum_for_date(date_iso: str) -> int:
    """Total recebido em uma data (YYYY-MM-DD) somando amount_cents dos pagamentos nessa data (UTC)."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount_cents), 0) FROM payments WHERE substr(created_at_iso, 1, 10) = ?",
            (date_iso,),
        ).fetchone()
        return int(row[0]) if row and row[0] is not None else 0
