"""Build and commit Gold from the existing Silver table."""

from pathlib import Path

import duckdb

from src.settings import PROJECT_ROOT
from src.stage_inputs import require_tables


def build_gold(database_path: Path) -> int:
    """Retry Gold without loading CSVs or rebuilding upstream layers."""
    require_tables(database_path, ["silver.sales_enriched"], "silver")
    with duckdb.connect(str(database_path)) as connection:
        connection.execute("BEGIN TRANSACTION")
        try:
            connection.execute("CREATE SCHEMA IF NOT EXISTS gold")
            connection.execute((PROJECT_ROOT / "sql/02_gold.sql").read_text(encoding="utf-8"))
            gold_count = connection.execute("SELECT count(*) FROM gold.monthly_sales_summary").fetchone()[0]
            if not gold_count:
                raise ValueError("The monthly sales summary contains no rows.")
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
    return gold_count
