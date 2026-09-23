"""Check that a stage's committed upstream tables exist."""

from pathlib import Path

import duckdb


def require_tables(database_path: Path, tables: list[str], upstream: str) -> None:
    if not database_path.is_file():
        raise ValueError(f"Database not found: {database_path}. Run --layer bronze first.")
    with duckdb.connect(str(database_path), read_only=True) as connection:
        available = {
            f"{schema}.{table}"
            for schema, table in connection.execute(
                "SELECT table_schema, table_name FROM information_schema.tables"
            ).fetchall()
        }
    missing = [table for table in tables if table not in available]
    if missing:
        raise ValueError(f"Missing upstream tables: {', '.join(missing)}. Run --layer {upstream} first.")
