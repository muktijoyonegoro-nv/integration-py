"""Low-level database helper utilities for MySQL."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

import pymysql


@dataclass
class IntraHubNodeRecord:
    id: int
    system_id: str
    hub_id: int
    type: str
    ref_hub_id: int
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


def parse_mysql_dsn(dsn: str) -> dict:
    """Parses standard DSN format: root:root@tcp(127.0.0.1:3306)/dbname?params."""
    pattern = r"^(?P<user>[^:]+):(?P<password>[^@]*)@tcp\((?P<host>[^:]+):(?P<port>\d+)\)/(?P<database>[^?]*)"
    m = re.match(pattern, dsn)
    if m:
        return {
            "user": m.group("user"),
            "password": m.group("password"),
            "host": m.group("host"),
            "port": int(m.group("port")),
            "database": m.group("database") or None,
        }
    # Fallback to standard urlparse
    u = urlparse(dsn)
    return {
        "user": u.username or "root",
        "password": u.password or "root",
        "host": u.hostname or "127.0.0.1",
        "port": u.port or 3306,
        "database": u.path.lstrip("/") or None,
    }


def connect_mysql(dsn: str, timeout: float = 10.0) -> pymysql.connections.Connection:
    """Establishes and tests a connection to MySQL, retrying until timeout."""
    params = parse_mysql_dsn(dsn)
    deadline = time.time() + timeout
    last_err: Optional[Exception] = None

    while time.time() < deadline:
        try:
            conn = pymysql.connect(
                host=params["host"],
                port=params["port"],
                user=params["user"],
                password=params["password"],
                database=params["database"],
                autocommit=True,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
            )
            conn.ping(reconnect=True)
            return conn
        except Exception as e:
            last_err = e
            time.sleep(0.3)

    raise ConnectionError(f"Failed to connect to MySQL at {dsn} within {timeout}s: {last_err}")


def truncate_tables(conn: pymysql.connections.Connection, tables: Optional[List[str]] = None) -> None:
    """Truncates specified tables across databases, disabling foreign key checks during truncation."""
    if not tables:
        tables = [
            "sort_mistake.intra_hub_nodes",
            "sort_service.intra_hub_nodes",
        ]

    with conn.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        try:
            for table in tables:
                try:
                    cursor.execute(f"TRUNCATE TABLE {table};")
                except pymysql.MySQLError as e:
                    # Ignore table doesn't exist (MySQL error 1146)
                    if e.args and e.args[0] == 1146:
                        continue
                    raise
        finally:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")


def query_intra_hub_node(
    conn: pymysql.connections.Connection,
    database_name: str,
    node_id: int,
) -> Optional[IntraHubNodeRecord]:
    """Queries an intra_hub_node by ID from the specified database."""
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
