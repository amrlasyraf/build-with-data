from pathlib import Path

import duckdb
import pandas as pd

from step_02_bronze.bronze import load_bronze_tables
from src.database import prepare_database
from step_02_bronze.source_validation import ValidatedSource


def test_load_bronze_tables_replaces_data_without_duplicates(tmp_path: Path) -> None:
    database_path = tmp_path / "retail_pipeline.duckdb"
    prepare_database(database_path)

    sources = [
        ValidatedSource(
            file_name="Sales.csv",
            table_name="sales",
            dataframe=pd.DataFrame(
                {
                    "order_number": ["1", "1"],
                    "line_item": ["1", "2"],
                    "order_date": ["1/1/2024", "1/1/2024"],
                    "delivery_date": ["", ""],
                    "customer_key": ["10", "10"],
                    "store_key": ["0", "0"],
                    "product_key": ["100", "101"],
                    "quantity": ["2", "1"],
                    "currency_code": ["USD", "USD"],
                }
            ),
        ),
        ValidatedSource(
            file_name="Products.csv",
            table_name="products",
            dataframe=pd.DataFrame(
                {
                    "product_key": ["100", "101"],
                    "product_name": ["Product A", "Product B"],
                    "brand": ["Brand", "Brand"],
                    "color": ["Black", "Blue"],
                    "unit_cost_usd": ["$10.00", "$12.00"],
                    "unit_price_usd": ["$20.00", "$24.00"],
                    "subcategory_key": ["01", "01"],
                    "subcategory": ["Example", "Example"],
                    "category_key": ["1", "1"],
                    "category": ["Test", "Test"],
                }
            ),
        ),
        ValidatedSource(
            file_name="Stores.csv",
            table_name="stores",
            dataframe=pd.DataFrame(
                {
                    "store_key": ["0"],
                    "country": ["Online"],
                    "state": ["Online"],
                    "square_meters": [""],
                    "open_date": ["1/1/2020"],
                }
            ),
        ),
    ]

    first_counts = load_bronze_tables(database_path, sources)
    second_counts = load_bronze_tables(database_path, sources)

    assert first_counts == {"sales": 2, "products": 2, "stores": 1}
    assert second_counts == first_counts

    with duckdb.connect(str(database_path), read_only=True) as connection:
        assert connection.execute(
            "SELECT count(*) FROM bronze.sales"
        ).fetchone()[0] == 2
        assert connection.execute(
            "SELECT count(DISTINCT source_file) FROM bronze.sales"
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT count(*) FROM bronze.sales WHERE loaded_at IS NULL"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT subcategory_key FROM bronze.products ORDER BY product_key LIMIT 1"
        ).fetchone()[0] == "01"
