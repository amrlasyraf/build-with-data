"""Build and commit Silver independently of Gold."""

from pathlib import Path

import duckdb

from src.settings import PROJECT_ROOT
from src.stage_inputs import require_tables


def build_silver(database_path: Path) -> int:
    """Read committed Bronze tables; rollback only Silver on failure."""
    require_tables(database_path, ["bronze.sales", "bronze.products", "bronze.stores"], "bronze")
    with duckdb.connect(str(database_path)) as connection:
        connection.execute("BEGIN TRANSACTION")
        try:
            connection.execute("CREATE SCHEMA IF NOT EXISTS silver")
            connection.execute((PROJECT_ROOT / "step_03_silver/silver.sql").read_text(encoding="utf-8"))
            source_count = connection.execute("SELECT count(*) FROM bronze.sales").fetchone()[0]
            silver_count = connection.execute("SELECT count(*) FROM silver.sales_enriched").fetchone()[0]
            missing_matches = connection.execute("""
                SELECT count(*) FROM silver.sales_enriched
                WHERE product_name IS NULL OR store_country IS NULL
            """).fetchone()[0]
            if not silver_count or silver_count != source_count or missing_matches:
                raise ValueError("Product/store joins failed: check empty sources, missing or duplicate dimension keys.")
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
    return silver_count
