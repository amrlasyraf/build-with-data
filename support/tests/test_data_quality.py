import duckdb

from step_06_optional.data_quality.run_checks import CHECKS, run_quality_checks
from support.pipeline.database import prepare_database


def create_valid_pipeline_tables(database_path):
    prepare_database(database_path)
    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            """
            CREATE TABLE bronze.sales AS SELECT
                '1' AS order_number, '1' AS line_item, '1' AS product_key,
                '0' AS store_key, '2' AS quantity
            """
        )
        connection.execute(
            "CREATE TABLE bronze.products AS SELECT '1' AS product_key"
        )
        connection.execute(
            "CREATE TABLE bronze.stores AS SELECT '0' AS store_key"
        )
        connection.execute(
            """
            CREATE TABLE silver.sales_enriched AS SELECT
                1 AS order_number, 1 AS line_item, DATE '2024-01-01' AS order_date,
                DATE '2024-01-02' AS delivery_date, 1 AS product_key, 0 AS store_key,
                2 AS quantity, 'Online' AS sales_channel,
                10.00::DECIMAL(12,2) AS unit_cost_usd,
                20.00::DECIMAL(12,2) AS unit_price_usd,
                40.00::DECIMAL(14,2) AS gross_sales_usd,
                20.00::DECIMAL(14,2) AS estimated_gross_profit_usd
            """
        )
        connection.execute(
            """
            CREATE TABLE gold.monthly_sales_summary AS SELECT
                DATE '2024-01-01' AS sales_month, 'Audio' AS product_category,
                'Online' AS sales_channel, 1::BIGINT AS line_item_count,
                2::BIGINT AS units_sold,
                40.00::DECIMAL(16,2) AS gross_sales_usd,
                20.00::DECIMAL(16,2) AS estimated_gross_profit_usd
            """
        )


def test_quality_results_append_and_expose_latest_run(tmp_path):
    database_path = tmp_path / "quality.duckdb"
    create_valid_pipeline_tables(database_path)

    first_run_id, first_results = run_quality_checks(database_path)
    assert all(result.status == "PASS" for result in first_results)

    with duckdb.connect(str(database_path)) as connection:
        connection.execute("INSERT INTO bronze.sales SELECT * FROM bronze.sales")

    second_run_id, second_results = run_quality_checks(database_path)
    assert second_run_id != first_run_id
    assert {
        result.name for result in second_results if result.status == "FAIL"
    } == {"sales_grain_unique", "silver_row_count_matches_bronze"}

    with duckdb.connect(str(database_path), read_only=True) as connection:
        quality_schema = '"quality"."quality"'
        assert connection.execute(
            f"SELECT count(*) FROM {quality_schema}.check_results"
        ).fetchone()[0] == len(CHECKS) * 2
        latest_run_ids = connection.execute(
            f"SELECT DISTINCT run_id::VARCHAR "
            f"FROM {quality_schema}.latest_check_results"
        ).fetchall()
        assert latest_run_ids == [(second_run_id,)]
