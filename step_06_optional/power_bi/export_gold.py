"""Export the Gold monthly summary as a Power BI-ready CSV file."""

from pathlib import Path

import duckdb

from support.pipeline.settings import DATABASE_PATH, LOCAL_DIR
from support.pipeline.stage_inputs import require_tables


DEFAULT_EXPORT_PATH = LOCAL_DIR / "exports" / "monthly_sales_summary.csv"


def export_gold_csv(
    database_path: Path = DATABASE_PATH,
    export_path: Path = DEFAULT_EXPORT_PATH,
) -> int:
    """Export committed Gold data in a stable order and return its row count."""
    require_tables(database_path, ["gold.monthly_sales_summary"], "gold")
    export_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = export_path.with_suffix(".tmp.csv")

    if temporary_path.exists():
        temporary_path.unlink()

    temporary_literal = str(temporary_path).replace("'", "''")
    try:
        with duckdb.connect(str(database_path), read_only=True) as connection:
            row_count = connection.execute(
                "SELECT count(*) FROM gold.monthly_sales_summary"
            ).fetchone()[0]
            if row_count == 0:
                raise ValueError("Gold is empty. Run the pipeline before exporting.")

            connection.execute(
                f"""
                COPY (
                    SELECT *
                    FROM gold.monthly_sales_summary
                    ORDER BY sales_month, product_category, sales_channel
                ) TO '{temporary_literal}' (FORMAT CSV, HEADER)
                """
            )

        temporary_path.replace(export_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    return row_count


def main() -> int:
    try:
        row_count = export_gold_csv()
    except (duckdb.Error, OSError, ValueError) as error:
        print(f"Power BI export failed: {error}")
        return 1

    print(f"Power BI CSV created: {DEFAULT_EXPORT_PATH}")
    print(f"Rows exported: {row_count:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
