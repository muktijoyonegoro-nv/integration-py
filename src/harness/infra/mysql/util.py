"""Low-level database helper utilities for MySQL."""

from __future__ import annotations

import re
import time
from collections.abc import Sequence
from urllib.parse import urlparse

import pymysql


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
    last_err: Exception | None = None

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
        except (pymysql.MySQLError, OSError) as e:
            last_err = e
            time.sleep(0.3)

    raise ConnectionError(f"Failed to connect to MySQL at {dsn} within {timeout}s: {last_err}")


def truncate_tables(conn: pymysql.connections.Connection, tables: Sequence[str]) -> None:
    """Truncates specified tables across databases, disabling foreign key checks during truncation."""
    if not tables:
        return

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
