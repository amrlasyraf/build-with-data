from datetime import date
from decimal import Decimal

import duckdb
import pandas as pd
import pytest

from step_02_bronze.bronze import SourceFile, load_bronze_tables
from support.pipeline.database import prepare_database
from step_03_silver.silver import build_silver
from step_04_gold.gold import build_gold
from step_04_gold import gold as gold_stage


def test_transformations_calculate_and_preserve_outputs_on_failure(tmp_path):
    path = tmp_path / "test.duckdb"
    prepare_database(path)
    sources = [
        SourceFile("Sales.csv", "sales", pd.DataFrame({
            "order_number": ["1", "2"], "line_item": ["1", "1"],
            "order_date": ["1/31/2024", "2/1/2024"],
            "delivery_date": ["", "2/3/2024"], "customer_key": ["1", "1"],
            "store_key": ["1", "0"], "product_key": ["1", "1"],
            "quantity": ["2", "3"], "currency_code": ["USD", "CAD"],
        })),
        SourceFile("Products.csv", "products", pd.DataFrame({
            "product_key": ["1"], "product_name": ["Example"], "brand": ["Test"],
            "subcategory": ["Test"], "category": ["Audio"],
            "unit_cost_usd": [" $1,000.10 "], "unit_price_usd": [" $1,200.25 "],
        })),
        SourceFile("Stores.csv", "stores", pd.DataFrame({
            "store_key": ["0", "1"], "country": ["Online", "US"],
            "state": ["Online", "Example"],
        })),
    ]
    load_bronze_tables(path, sources)
    for _ in range(2):
        assert build_silver(path) == 2
        assert build_gold(path) == 2
    with duckdb.connect(str(path)) as con:
        assert con.execute("SELECT delivery_date FROM silver.sales_enriched ORDER BY order_number").fetchall() == [(None,), (date(2024, 2, 3),)]
        expected = [
            (date(2024, 1, 1), "In Store", 2, Decimal("2400.50"), Decimal("400.30")),
            (date(2024, 2, 1), "Online", 3, Decimal("3600.75"), Decimal("600.45")),
        ]
        query = "SELECT sales_month, sales_channel, units_sold, gross_sales_usd, estimated_gross_profit_usd FROM gold.monthly_sales_summary ORDER BY sales_month"
        assert con.execute(query).fetchall() == expected
        con.execute("UPDATE bronze.sales SET product_key = '999' WHERE order_number = '1'")
    with pytest.raises(ValueError, match="joins failed"):
        build_silver(path)
    with duckdb.connect(str(path)) as con:
        assert con.execute(query).fetchall() == expected
        assert con.execute("SELECT product_key FROM silver.sales_enriched WHERE order_number = 1").fetchone() == (1,)
        con.execute("UPDATE bronze.sales SET order_date = 'invalid'")
    with pytest.raises(ValueError, match="sales date"):
        build_silver(path)
    with duckdb.connect(str(path)) as con:
        assert con.execute(query).fetchall() == expected
        con.execute("UPDATE bronze.sales SET product_key = '1', order_date = '2/1/2024' WHERE order_number = '2'")
        con.execute("UPDATE bronze.sales SET product_key = '1', order_date = '' WHERE order_number = '1'")
    with pytest.raises(ValueError, match="order_date is required"):
        build_silver(path)
    with duckdb.connect(str(path)) as con:
        assert con.execute(query).fetchall() == expected
        assert con.execute("SELECT order_date FROM silver.sales_enriched WHERE order_number = 1").fetchone() == (date(2024, 1, 31),)
        con.execute("UPDATE bronze.sales SET order_date = '1/31/2024' WHERE order_number = '1'")
        con.execute("UPDATE bronze.products SET category = '' WHERE product_key = '1'")
    with pytest.raises(ValueError, match="product_category is required"):
        build_silver(path)
    with duckdb.connect(str(path)) as con:
        assert con.execute(query).fetchall() == expected


def test_gold_failure_and_retry_do_not_change_silver(tmp_path, monkeypatch):
    path = tmp_path / "retry.duckdb"
    prepare_database(path)
    with duckdb.connect(str(path)) as con:
        con.execute("""
            CREATE TABLE silver.sales_enriched AS
            SELECT DATE '2024-01-01' AS order_date, 'Audio' AS product_category,
                   'Online' AS sales_channel, 2 AS quantity,
                   20.00 AS gross_sales_usd, 8.00 AS estimated_gross_profit_usd,
                   current_timestamp AS loaded_at
        """)
    assert build_gold(path) == 1
    with duckdb.connect(str(path)) as con:
        old_gold = con.execute("SELECT * FROM gold.monthly_sales_summary").fetchall()
        con.execute("UPDATE silver.sales_enriched SET order_date = NULL")
    with pytest.raises(ValueError, match="order_date is required"):
        build_gold(path)
    with duckdb.connect(str(path)) as con:
        assert con.execute("SELECT * FROM gold.monthly_sales_summary").fetchall() == old_gold
        con.execute("UPDATE silver.sales_enriched SET order_date = DATE '2024-01-01'")
        con.execute("UPDATE silver.sales_enriched SET product_category = ''")
    with pytest.raises(ValueError, match="product_category is required"):
        build_gold(path)
    with duckdb.connect(str(path)) as con:
        assert con.execute("SELECT * FROM gold.monthly_sales_summary").fetchall() == old_gold
        con.execute("UPDATE silver.sales_enriched SET product_category = 'Audio'")
    original_aggregate = gold_stage.aggregate_gold
    with monkeypatch.context() as patch:
        def wrong_count(sales):
            summary = original_aggregate(sales)
            summary["line_item_count"] = 0
            return summary
        patch.setattr(gold_stage, "aggregate_gold", wrong_count)
        with pytest.raises(ValueError, match="do not reconcile"):
            build_gold(path)
    with duckdb.connect(str(path)) as con:
        assert con.execute("SELECT * FROM gold.monthly_sales_summary").fetchall() == old_gold
        # A committed upstream value that cannot fit Gold's DECIMAL(16,2).
        con.execute("ALTER TABLE silver.sales_enriched ALTER gross_sales_usd TYPE DECIMAL(30,2)")
        con.execute("UPDATE silver.sales_enriched SET gross_sales_usd = 1000000000000000")
        silver_before = con.execute("SELECT * FROM silver.sales_enriched").fetchall()
    with pytest.raises(duckdb.Error):
        build_gold(path)
    with duckdb.connect(str(path)) as con:
        assert con.execute("SELECT * FROM silver.sales_enriched").fetchall() == silver_before
        assert con.execute("SELECT * FROM gold.monthly_sales_summary").fetchall() == old_gold
        con.execute("UPDATE silver.sales_enriched SET gross_sales_usd = 40.00")
        corrected_silver = con.execute("SELECT * FROM silver.sales_enriched").fetchall()
    for _ in range(2):
        assert build_gold(path) == 1
    with duckdb.connect(str(path)) as con:
        assert con.execute("SELECT * FROM silver.sales_enriched").fetchall() == corrected_silver
        assert con.execute("SELECT gross_sales_usd FROM gold.monthly_sales_summary").fetchone() == (Decimal("40.00"),)


def test_missing_dependencies_do_not_create_database(tmp_path):
    path = tmp_path / "missing.duckdb"
    with pytest.raises(ValueError, match="Run bronze.py first"):
        build_gold(path)
    assert not path.exists()
    prepare_database(path)
    with pytest.raises(ValueError, match="Run silver.py first"):
        build_gold(path)
