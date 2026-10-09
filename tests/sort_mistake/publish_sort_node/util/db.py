"""Database query helpers for sort_mistake."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pymysql


@dataclass
class IntraHubNodeRecord:
    id: int
    system_id: str
    hub_id: int
    type: str
    ref_hub_id: int
    name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


def query_intra_hub_node(
    conn: pymysql.connections.Connection,
    node_id: int,
    database_name: str = "sort_mistake",
) -> IntraHubNodeRecord | None:
    """Queries an intra_hub_node by ID from sort_mistake database."""
    query = f"""
        SELECT id, system_id, hub_id, type, ref_hub_id, name, created_at, updated_at
        FROM {database_name}.intra_hub_nodes
        WHERE id = %s
    """
    with conn.cursor() as cursor:
        cursor.execute(query, (node_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return IntraHubNodeRecord(
            id=row["id"],
            system_id=row["system_id"],
            hub_id=row["hub_id"],
            type=row["type"],
            ref_hub_id=row["ref_hub_id"],
            name=row["name"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
