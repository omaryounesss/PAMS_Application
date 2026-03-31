"""Database access layer backed by mysql-connector connection pooling."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from app.config import DatabaseConfig

try:
    import mysql.connector
    from mysql.connector import pooling
except ModuleNotFoundError as exc:  # pragma: no cover - runtime dependency guard
    raise ModuleNotFoundError(
        "mysql-connector-python is required. Install with: pip install mysql-connector-python"
    ) from exc


class Database:
    def __init__(self, cfg: DatabaseConfig) -> None:
        self._cfg = cfg
        self._pool = pooling.MySQLConnectionPool(
            pool_name=cfg.pool_name,
            pool_size=cfg.pool_size,
            host=cfg.host,
            port=cfg.port,
            user=cfg.user,
            password=cfg.password,
            database=cfg.database,
            autocommit=False,
        )

    @contextmanager
    def connection(self):
        conn = self._pool.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
        *,
        fetchone: bool = False,
        fetchall: bool = False,
    ) -> Any:
        params = params or ()
        with self.connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(query, params)
                if fetchone:
                    return cursor.fetchone()
                if fetchall:
                    return cursor.fetchall()
                statement = query.lstrip().upper()
                if statement.startswith("INSERT"):
                    return cursor.lastrowid
                return cursor.rowcount

    def executemany(self, query: str, seq_params: list[tuple[Any, ...]]) -> int:
        with self.connection() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(query, seq_params)
                return cursor.rowcount
