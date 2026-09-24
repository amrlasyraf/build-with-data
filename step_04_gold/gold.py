"""Aggregate Silver with pandas, then commit Gold independently."""

from pathlib import Path
import sys

# VS Code's Run button starts this file directly, outside the project package.
if __name__ == "__main__" and not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb
import pandas as pd

from support.pipeline.stage_inputs import require_tables
from support.pipeline.settings import DATABASE_PATH


def aggregate_gold(sales: pd.DataFrame) -> pd.DataFrame:
    """Return monthly category/channel totals from cleaned sales lines."""
    if sales.empty:
        raise ValueError("Silver sales is empty. Run Silver first.")
    sales = sales.copy()
    sales["sales_month"] = pd.to_datetime(sales["order_date"]).dt.to_period("M").dt.to_timestamp()
    return sales.groupby(
        ["sales_month", "product_category", "sales_channel"],
        as_index=False,
        sort=True,
    ).agg(
        line_item_count=("quantity", "size"),
        units_sold=("quantity", "sum"),
        gross_sales_usd=("gross_sales_usd", "sum"),
        estimated_gross_profit_usd=("estimated_gross_profit_usd", "sum"),
    )


def build_gold(database_path: Path) -> int:
    """Read committed Silver; replace only Gold or leave it unchanged."""
    require_tables(database_path, ["silver.sales_enriched"], "silver")
    with duckdb.connect(str(database_path)) as connection:
        connection.execute("BEGIN TRANSACTION")
        try:
            query = connection.execute("""
                SELECT order_date, product_category, sales_channel, quantity,
                       gross_sales_usd, estimated_gross_profit_usd
                FROM silver.sales_enriched
            """)
            # fetchall preserves Decimal values; .df() would turn them into floats.
            sales = pd.DataFrame(query.fetchall(), columns=[column[0] for column in query.description])
            summary = aggregate_gold(sales)
            connection.register("gold_frame", summary)
            try:
                connection.execute("CREATE SCHEMA IF NOT EXISTS gold")
                connection.execute("""
                    CREATE OR REPLACE TABLE gold.monthly_sales_summary AS
                    SELECT CAST(sales_month AS DATE) AS sales_month,
                           product_category, sales_channel,
                           CAST(line_item_count AS BIGINT) AS line_item_count,
                           CAST(units_sold AS BIGINT) AS units_sold,
                           CAST(gross_sales_usd AS DECIMAL(16,2)) AS gross_sales_usd,
                           CAST(estimated_gross_profit_usd AS DECIMAL(16,2))
                               AS estimated_gross_profit_usd
                    FROM gold_frame
                """)
            finally:
                connection.unregister("gold_frame")

            gold_count = connection.execute("SELECT count(*) FROM gold.monthly_sales_summary").fetchone()[0]
            if not gold_count or gold_count != len(summary):
                raise ValueError("Gold summary row count does not match the pandas result")
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
    return gold_count


def main() -> int:
    """Build Gold when this file is run from VS Code."""
    try:
        count = build_gold(DATABASE_PATH)
    except (duckdb.Error, ValueError, OSError, RuntimeError, KeyError) as error:
        print(f"Gold failed: {error}")
        return 1
    print(f"Gold complete: {count:,} rows in gold.monthly_sales_summary")
    print(f"Database: {DATABASE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
