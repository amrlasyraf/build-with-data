"""Run optional data-quality checks against committed pipeline tables."""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import duckdb

from support.pipeline.settings import DATABASE_PATH
from support.pipeline.stage_inputs import require_tables


@dataclass(frozen=True)
class QualityCheck:
    name: str
    layer: str
    severity: str
    description: str
    sql: str


@dataclass(frozen=True)
class CheckResult:
    name: str
    layer: str
    severity: str
    status: str
    failed_rows: int
    total_rows: int
    failure_rate: float
    description: str


CHECKS = [
    QualityCheck(
        "required_tables_not_empty",
        "all",
        "critical",
        "The five core pipeline tables contain at least one row.",
        """
        SELECT
            CAST(
                (SELECT count(*) = 0 FROM bronze.sales)::INTEGER
              + (SELECT count(*) = 0 FROM bronze.products)::INTEGER
              + (SELECT count(*) = 0 FROM bronze.stores)::INTEGER
              + (SELECT count(*) = 0 FROM silver.sales_enriched)::INTEGER
              + (SELECT count(*) = 0 FROM gold.monthly_sales_summary)::INTEGER
                AS BIGINT
            ) AS failed_rows,
            5::BIGINT AS total_rows
        """,
    ),
    QualityCheck(
        "sales_grain_unique",
        "bronze",
        "critical",
        "Each order number and line item identifies one sales row.",
        """
        SELECT coalesce(sum(rows_per_key - 1), 0)::BIGINT AS failed_rows,
               (SELECT count(*) FROM bronze.sales)::BIGINT AS total_rows
        FROM (
            SELECT count(*) AS rows_per_key
            FROM bronze.sales
            GROUP BY order_number, line_item
            HAVING count(*) > 1
        ) AS duplicate_keys
        """,
    ),
    QualityCheck(
        "product_key_unique",
        "bronze",
        "critical",
        "Each product key identifies one product row.",
        """
        SELECT coalesce(sum(rows_per_key - 1), 0)::BIGINT AS failed_rows,
               (SELECT count(*) FROM bronze.products)::BIGINT AS total_rows
        FROM (
            SELECT count(*) AS rows_per_key
            FROM bronze.products
            GROUP BY product_key
            HAVING count(*) > 1
        ) AS duplicate_keys
        """,
    ),
    QualityCheck(
        "store_key_unique",
        "bronze",
        "critical",
        "Each store key identifies one store row.",
        """
        SELECT coalesce(sum(rows_per_key - 1), 0)::BIGINT AS failed_rows,
               (SELECT count(*) FROM bronze.stores)::BIGINT AS total_rows
        FROM (
            SELECT count(*) AS rows_per_key
            FROM bronze.stores
            GROUP BY store_key
            HAVING count(*) > 1
        ) AS duplicate_keys
        """,
    ),
    QualityCheck(
        "sales_product_keys_match",
        "bronze",
        "critical",
        "Every sales product key matches the product dimension.",
        """
        SELECT count(*) FILTER (WHERE p.product_key IS NULL)::BIGINT AS failed_rows,
               count(*)::BIGINT AS total_rows
        FROM bronze.sales AS s
        LEFT JOIN bronze.products AS p ON s.product_key = p.product_key
        """,
    ),
    QualityCheck(
        "sales_store_keys_match",
        "bronze",
        "critical",
        "Every sales store key matches the store dimension.",
        """
        SELECT count(*) FILTER (WHERE st.store_key IS NULL)::BIGINT AS failed_rows,
               count(*)::BIGINT AS total_rows
        FROM bronze.sales AS s
        LEFT JOIN bronze.stores AS st ON s.store_key = st.store_key
        """,
    ),
    QualityCheck(
        "quantity_positive_integer",
        "bronze",
        "high",
        "Sales quantity is a positive integer.",
        """
        WITH quantities AS (
            SELECT quantity,
                   try_cast(quantity AS DECIMAL(38,18)) AS number
            FROM bronze.sales
        )
        SELECT count(*) FILTER (
                   WHERE number IS NULL
                      OR number <= 0
                      OR number % 1 <> 0
                      OR try_cast(quantity AS BIGINT) IS NULL
               )::BIGINT AS failed_rows,
               count(*)::BIGINT AS total_rows
        FROM quantities
        """,
    ),
    QualityCheck(
        "delivery_not_before_order",
        "silver",
        "high",
        "A populated delivery date is on or after the order date.",
        """
        SELECT count(*) FILTER (WHERE delivery_date < order_date)::BIGINT AS failed_rows,
               count(*)::BIGINT AS total_rows
        FROM silver.sales_enriched
        """,
    ),
    QualityCheck(
        "online_orders_have_delivery_date",
        "silver",
        "high",
        "Online orders have a delivery date.",
        """
        SELECT count(*) FILTER (
                   WHERE sales_channel = 'Online' AND delivery_date IS NULL
               )::BIGINT AS failed_rows,
               count(*) FILTER (WHERE sales_channel = 'Online')::BIGINT AS total_rows
        FROM silver.sales_enriched
        """,
    ),
    QualityCheck(
        "silver_row_count_matches_bronze",
        "silver",
        "critical",
        "The Silver join neither loses nor multiplies sales rows.",
        """
        SELECT abs(
                   (SELECT count(*) FROM silver.sales_enriched)
                 - (SELECT count(*) FROM bronze.sales)
               )::BIGINT AS failed_rows,
               greatest(
                   (SELECT count(*) FROM silver.sales_enriched),
                   (SELECT count(*) FROM bronze.sales)
               )::BIGINT AS total_rows
        """,
    ),
    QualityCheck(
        "silver_measures_complete",
        "silver",
        "high",
        "Silver price, cost, sales, and estimated-profit measures are populated.",
        """
        SELECT count(*) FILTER (
                   WHERE unit_cost_usd IS NULL
                      OR unit_price_usd IS NULL
                      OR gross_sales_usd IS NULL
                      OR estimated_gross_profit_usd IS NULL
               )::BIGINT AS failed_rows,
               count(*)::BIGINT AS total_rows
        FROM silver.sales_enriched
        """,
    ),
    QualityCheck(
        "sales_channel_allowed_values",
        "silver",
        "high",
        "Sales channel is either Online or In Store.",
        """
        SELECT count(*) FILTER (
                   WHERE sales_channel NOT IN ('Online', 'In Store')
                      OR sales_channel IS NULL
               )::BIGINT AS failed_rows,
               count(*)::BIGINT AS total_rows
        FROM silver.sales_enriched
        """,
    ),
    QualityCheck(
        "gold_grain_unique",
        "gold",
        "critical",
        "Each month, product category, and channel appears once in Gold.",
        """
        SELECT coalesce(sum(rows_per_key - 1), 0)::BIGINT AS failed_rows,
               (SELECT count(*) FROM gold.monthly_sales_summary)::BIGINT AS total_rows
        FROM (
            SELECT count(*) AS rows_per_key
            FROM gold.monthly_sales_summary
            GROUP BY sales_month, product_category, sales_channel
            HAVING count(*) > 1
        ) AS duplicate_keys
        """,
    ),
    QualityCheck(
        "gold_totals_match_silver",
        "gold",
        "critical",
        "Gold units, sales, and estimated profit reconcile to Silver.",
        """
        WITH silver_totals AS (
            SELECT sum(quantity) AS units,
                   sum(gross_sales_usd) AS sales,
                   sum(estimated_gross_profit_usd) AS profit
            FROM silver.sales_enriched
        ), gold_totals AS (
            SELECT sum(units_sold) AS units,
                   sum(gross_sales_usd) AS sales,
                   sum(estimated_gross_profit_usd) AS profit
            FROM gold.monthly_sales_summary
        )
        SELECT CASE
                   WHEN s.units = g.units
                    AND s.sales = g.sales
                    AND s.profit = g.profit THEN 0
                   ELSE 1
               END::BIGINT AS failed_rows,
               1::BIGINT AS total_rows
        FROM silver_totals AS s
        CROSS JOIN gold_totals AS g
        """,
    ),
]


def require_quality_inputs(database_path: Path) -> None:
    require_tables(
        database_path,
        ["bronze.sales", "bronze.products", "bronze.stores"],
        "bronze",
    )
    require_tables(database_path, ["silver.sales_enriched"], "silver")
    require_tables(database_path, ["gold.monthly_sales_summary"], "gold")


def run_quality_checks(database_path: Path) -> tuple[str, list[CheckResult]]:
    """Execute stable checks and append an auditable result set."""
    require_quality_inputs(database_path)
    run_id = str(uuid4())
    checked_at = datetime.now(timezone.utc)
    results: list[CheckResult] = []

    with duckdb.connect(str(database_path)) as connection:
        catalog_name = connection.execute("SELECT current_database()").fetchone()[0]
        quoted_catalog = '"' + catalog_name.replace('"', '""') + '"'
        quality_schema = f'{quoted_catalog}."quality"'

        for check in CHECKS:
            failed_rows, total_rows = connection.execute(check.sql).fetchone()
            failed_rows = int(failed_rows)
            total_rows = int(total_rows)
            failure_rate = failed_rows / total_rows if total_rows else 0.0
            results.append(
                CheckResult(
                    name=check.name,
                    layer=check.layer,
                    severity=check.severity,
                    status="PASS" if failed_rows == 0 else "FAIL",
                    failed_rows=failed_rows,
                    total_rows=total_rows,
                    failure_rate=failure_rate,
                    description=check.description,
                )
            )

        connection.execute("BEGIN TRANSACTION")
        try:
            connection.execute(f"CREATE SCHEMA IF NOT EXISTS {quality_schema}")
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {quality_schema}.check_results (
                    run_id UUID NOT NULL,
                    checked_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    check_name VARCHAR NOT NULL,
                    layer VARCHAR NOT NULL,
                    severity VARCHAR NOT NULL,
                    status VARCHAR NOT NULL,
                    failed_rows BIGINT NOT NULL,
                    total_rows BIGINT NOT NULL,
                    failure_rate DOUBLE NOT NULL,
                    description VARCHAR NOT NULL
                )
                """
            )
            connection.executemany(
                f"INSERT INTO {quality_schema}.check_results "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        run_id,
                        checked_at,
                        result.name,
                        result.layer,
                        result.severity,
                        result.status,
                        result.failed_rows,
                        result.total_rows,
                        result.failure_rate,
                        result.description,
                    )
                    for result in results
                ],
            )
            connection.execute(
                f"""
                CREATE OR REPLACE VIEW {quality_schema}.latest_check_results AS
                SELECT *
                FROM {quality_schema}.check_results
                WHERE run_id = (
                    SELECT run_id
                    FROM {quality_schema}.check_results
                    ORDER BY checked_at DESC
                    LIMIT 1
                )
                """
            )
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise

    return run_id, results


def main() -> int:
    try:
        run_id, results = run_quality_checks(DATABASE_PATH)
    except (duckdb.Error, OSError, ValueError) as error:
        print(f"Data-quality run failed: {error}")
        return 1

    print(f"Data-quality run: {run_id}")
    print(f"{'STATUS':<7} {'SEVERITY':<9} {'LAYER':<8} {'FAILED':>8}  CHECK")
    for result in results:
        print(
            f"{result.status:<7} {result.severity.upper():<9} "
            f"{result.layer:<8} {result.failed_rows:>8,}  {result.name}"
        )

    failed_checks = [result for result in results if result.status == "FAIL"]
    if failed_checks:
        print(f"Data quality failed: {len(failed_checks)} check(s) need attention.")
        print("Inspect quality.latest_check_results for rates and descriptions.")
        return 1

    print(f"Data quality passed: all {len(results)} checks succeeded.")
    print("Results were appended to quality.check_results.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
