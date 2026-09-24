from decimal import Decimal

import duckdb

from step_02_bronze.bronze import load_bronze_tables, read_sources
from step_03_silver.silver import build_silver
from step_04_gold.gold import build_gold
from step_05_optional.data_quality.run_checks import run_quality_checks
from support.pipeline.database import prepare_database
from support.pipeline.settings import DATASET_DIR


def test_bundled_csvs_produce_expected_gold_totals(tmp_path):
    database_path = tmp_path / "retail.duckdb"
    prepare_database(database_path)
    counts = load_bronze_tables(database_path, read_sources(DATASET_DIR))
    assert counts == {"sales": 62884, "products": 2517, "stores": 67}
    assert build_silver(database_path) == 62884
    assert build_gold(database_path) == 979

    with duckdb.connect(str(database_path), read_only=True) as connection:
        actual = connection.execute("""
            SELECT count(*), sum(units_sold), sum(gross_sales_usd),
                   sum(estimated_gross_profit_usd)
            FROM gold.monthly_sales_summary
        """).fetchone()
        silver_types = dict(
            (row[0], row[1]) for row in connection.execute(
                "DESCRIBE silver.sales_enriched"
            ).fetchall()
        )
        gold_types = dict(
            (row[0], row[1]) for row in connection.execute(
                "DESCRIBE gold.monthly_sales_summary"
            ).fetchall()
        )

    assert actual == (
        979, 197757, Decimal("55755479.59"), Decimal("32662688.38")
    )
    assert silver_types["order_date"] == "DATE"
    assert silver_types["gross_sales_usd"] == "DECIMAL(14,2)"
    assert gold_types["sales_month"] == "DATE"
    assert gold_types["gross_sales_usd"] == "DECIMAL(16,2)"
    _, quality_results = run_quality_checks(database_path)
    assert all(result.status == "PASS" for result in quality_results)
