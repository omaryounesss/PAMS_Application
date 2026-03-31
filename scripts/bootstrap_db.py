"""Bootstrap MySQL database schema and seed data for PAMS."""

from __future__ import annotations

import os
from pathlib import Path

try:
    import mysql.connector
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit(
        "mysql-connector-python is required. Run: pip install mysql-connector-python"
    ) from exc

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "sql" / "schema.sql"
SEED_PATH = ROOT / "sql" / "seed.sql"

DB_HOST = os.getenv("PAMS_DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("PAMS_DB_PORT", "3306"))
DB_USER = os.getenv("PAMS_DB_USER", "root")
DB_PASSWORD = os.getenv("PAMS_DB_PASSWORD", "")


def load_sql_statements(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    statements: list[str] = []
    current: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(current))
            current = []

    if current:
        statements.append("\n".join(current))
    return statements


def execute_sql_file(cursor, path: Path) -> None:
    for stmt in load_sql_statements(path):
        cursor.execute(stmt)


def main() -> None:
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        autocommit=False,
    )
    try:
        cur = conn.cursor()
        print("Applying schema...")
        execute_sql_file(cur, SCHEMA_PATH)
        print("Applying seed data...")
        execute_sql_file(cur, SEED_PATH)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print("Done.")
    print("Seed users:")
    print("- admin_bristol / Admin@123")
    print("- frontdesk_bristol / Front@123")
    print("- finance_bristol / Finance@123")
    print("- maintenance_bristol / Maintain@123")
    print("- manager_uk / Manager@123")
    print("- admin_cardiff / Admin@123")
    print("- tenant_hamdy / Tenant@123")
    print("- tenant_alabweh / Tenant@123")
    print("- tenant_younes / Tenant@123")
    print("- tenant_sharaf / Tenant@123")
    print("- tenant_nadine / Tenant@123")
    print("- tenant_yousef / Tenant@123")
    print("- tenant_mariam / Tenant@123")
    print("- tenant_nour / Tenant@123")


if __name__ == "__main__":
    main()
