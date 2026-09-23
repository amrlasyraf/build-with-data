import csv
from pathlib import Path

import duckdb

from step_06_optional.power_bi.export_gold import export_gold_csv
from support.pipeline.database import prepare_database


def test_export_gold_csv_writes_ordered_rows(tmp_path: Path) -> None:
    database_path = tmp_path / "retail_pipeline.duckdb"
    export_path = tmp_path / "exports" / "monthly_sales_summary.csv"
    prepare_database(database_path)

    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            """
            CREATE TABLE gold.monthly_sales_summary (
                sales_month DATE,
                product_category VARCHAR,
                sales_channel VARCHAR,
                line_item_count BIGINT,
                units_sold BIGINT,
                gross_sales_usd DECIMAL(16, 2),
                estimated_gross_profit_usd DECIMAL(16, 2)
            )
            """
        )
        connection.execute(
            """
            INSERT INTO gold.monthly_sales_summary VALUES
                ('2024-02-01', 'Audio', 'Online', 2, 3, 120.00, 40.00),
                ('2024-01-01', 'Computers', 'In Store', 1, 1, 500.00, 150.00)
            """
        )

    row_count = export_gold_csv(database_path, export_path)

    with export_path.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert row_count == 2
    assert len(rows) == 2
    assert rows[0]["sales_month"] == "2024-01-01"
    assert rows[1]["sales_month"] == "2024-02-01"
    assert rows[0]["gross_sales_usd"] == "500.00"
