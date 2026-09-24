from datetime import date

import duckdb
import pandas as pd
import pytest

pytest.importorskip("sklearn")

from step_05_optional.forecasting.run_forecast import (
    add_features,
    complete_months,
    last_complete_month,
    run_forecast,
)
from support.pipeline.database import prepare_database


def test_last_partial_month_is_excluded() -> None:
    assert last_complete_month(date(2021, 2, 20)) == pd.Timestamp("2021-01-01")
    assert last_complete_month(date(2020, 2, 29)) == pd.Timestamp("2020-02-01")


def test_missing_month_is_zero_and_lags_use_only_prior_actuals() -> None:
    monthly = pd.DataFrame(
        {
            "sales_month": pd.to_datetime(["2024-01-01", "2024-03-01"]),
            "product_category": ["Audio", "Audio"],
            "sales_channel": ["Online", "Online"],
            "gross_sales_usd": [100.0, 300.0],
        }
    )
    panel = complete_months(monthly, pd.Timestamp("2024-03-01"))
    featured = add_features(panel)

    assert panel["gross_sales_usd"].tolist() == [100.0, 0.0, 300.0]
    assert featured["lag_1"].iloc[2] == 0.0
    assert pd.isna(featured["lag_1"].iloc[0])


def test_forecast_writes_local_outputs_without_changing_silver(tmp_path) -> None:
    database_path = tmp_path / "pipeline.duckdb"
    output_dir = tmp_path / "forecasts"
    prepare_database(database_path)
    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            """
            CREATE TABLE silver.sales_enriched (
                order_date DATE,
                product_category VARCHAR,
                sales_channel VARCHAR,
                gross_sales_usd DOUBLE
            )
            """
        )
        connection.execute(
            """
            INSERT INTO silver.sales_enriched
            SELECT month::DATE, 'Audio', 'Online',
                   100.0 + 5.0 * row_number() OVER (ORDER BY month)
            FROM generate_series(DATE '2020-01-01', DATE '2024-01-01',
                                 INTERVAL '1 month') AS dates(month)
            """
        )
        connection.execute(
            "INSERT INTO silver.sales_enriched VALUES ('2024-02-10', 'Audio', 'Online', 9999.0)"
        )
        before = connection.execute("SELECT count(*) FROM silver.sales_enriched").fetchone()[0]

    summary = run_forecast(database_path, output_dir)

    assert summary["last_complete_month"] == "2024-01-01"
    assert summary["holdout_start"] == "2023-02-01"
    assert summary["next_forecast_month"] == "2024-02-01"
    assert len(pd.read_csv(output_dir / "holdout_predictions.csv")) == 12
    assert len(pd.read_csv(output_dir / "next_month_forecast.csv")) == 1
    assert (output_dir / "metrics.json").is_file()
    with duckdb.connect(str(database_path), read_only=True) as connection:
        assert connection.execute("SELECT count(*) FROM silver.sales_enriched").fetchone()[0] == before
