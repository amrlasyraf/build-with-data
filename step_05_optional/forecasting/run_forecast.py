"""Compare a simple model with a seasonal baseline using Silver sales."""

import calendar
import json
from pathlib import Path

import duckdb
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from support.pipeline.settings import DATABASE_PATH, LOCAL_DIR


OUTPUT_DIR = LOCAL_DIR / "forecasts"
HOLDOUT_MONTHS = 12
NUMERIC_FEATURES = ["lag_1", "lag_12", "previous_3_month_average"]
CATEGORICAL_FEATURES = ["product_category", "sales_channel", "month_number"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def last_complete_month(latest_order_date) -> pd.Timestamp:
    """Exclude a final month unless the source reaches its last calendar day."""
    latest = pd.Timestamp(latest_order_date)
    if latest.day != calendar.monthrange(latest.year, latest.month)[1]:
        latest -= pd.DateOffset(months=1)
    return latest.to_period("M").to_timestamp()


def load_monthly_sales(database_path: Path) -> tuple[pd.DataFrame, pd.Timestamp, str | None]:
    if not database_path.is_file():
        raise FileNotFoundError("Silver database not found. Run Bronze and Silver first.")

    with duckdb.connect(str(database_path), read_only=True) as connection:
        latest_date = connection.execute(
            "SELECT max(order_date) FROM silver.sales_enriched"
        ).fetchone()[0]
        if latest_date is None:
            raise ValueError("Silver sales is empty. Run Silver first.")
        last_month = last_complete_month(latest_date)
        latest_month = pd.Timestamp(latest_date).to_period("M").to_timestamp()
        excluded_month = (
            latest_month.strftime("%Y-%m-%d") if latest_month > last_month else None
        )
        monthly = connection.execute(
            """
            SELECT date_trunc('month', order_date)::DATE AS sales_month,
                   product_category, sales_channel,
                   sum(gross_sales_usd)::DOUBLE AS gross_sales_usd
            FROM silver.sales_enriched
            WHERE order_date < ?
            GROUP BY 1, 2, 3
            ORDER BY 1, 2, 3
            """,
            [last_month + pd.DateOffset(months=1)],
        ).df()

    monthly["sales_month"] = pd.to_datetime(monthly["sales_month"])
    return monthly, last_month, excluded_month


def complete_months(monthly: pd.DataFrame, last_month: pd.Timestamp) -> pd.DataFrame:
    """Treat an absent category/channel month as zero observed sales."""
    if monthly.empty:
        raise ValueError("No complete months in Silver sales to forecast.")
    first_month = monthly["sales_month"].min()
    months = pd.date_range(first_month, last_month, freq="MS")
    segments = monthly[["product_category", "sales_channel"]].drop_duplicates()
    grid = pd.MultiIndex.from_product(
        [months, segments.itertuples(index=False, name=None)],
        names=["sales_month", "segment"],
    ).to_frame(index=False)
    grid[["product_category", "sales_channel"]] = pd.DataFrame(
        grid.pop("segment").tolist(), index=grid.index
    )
    panel = grid.merge(
        monthly,
        on=["sales_month", "product_category", "sales_channel"],
        how="left",
        validate="one_to_one",
    )
    panel["gross_sales_usd"] = panel["gross_sales_usd"].fillna(0.0)
    return panel.sort_values(
        ["product_category", "sales_channel", "sales_month"]
    ).reset_index(drop=True)


def add_features(panel: pd.DataFrame) -> pd.DataFrame:
    result = panel.copy()
    by_segment = result.groupby(["product_category", "sales_channel"])["gross_sales_usd"]
    result["lag_1"] = by_segment.shift(1)
    result["lag_12"] = by_segment.shift(12)
    result["previous_3_month_average"] = by_segment.transform(
        lambda values: values.shift(1).rolling(3).mean()
    )
    result["month_number"] = result["sales_month"].dt.month.astype(str)
    return result


def make_model():
    processor = ColumnTransformer(
        [
            ("amounts", StandardScaler(), NUMERIC_FEATURES),
            ("labels", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )
    return make_pipeline(processor, Ridge(alpha=10.0))


def summarize_errors(actual: pd.Series, predicted: pd.Series) -> dict[str, float | None]:
    absolute_errors = (actual - predicted).abs()
    total_actual = actual.sum()
    return {
        "mae_usd": round(float(absolute_errors.mean()), 2),
        "wape_percent": round(float(100 * absolute_errors.sum() / total_actual), 2)
        if total_actual else None,
    }


def run_forecast(database_path: Path = DATABASE_PATH, output_dir: Path = OUTPUT_DIR) -> dict:
    monthly, last_month, excluded_month = load_monthly_sales(database_path)
    panel = complete_months(monthly, last_month)
    history = add_features(panel).dropna(subset=NUMERIC_FEATURES).copy()
    months = sorted(history["sales_month"].unique())
    if len(months) < HOLDOUT_MONTHS * 2:
        raise ValueError("Need at least 24 months after the first 12-month lag.")

    test_start = months[-HOLDOUT_MONTHS]
    train = history[history["sales_month"] < test_start]
    test = history[history["sales_month"] >= test_start].copy()
    model = make_model()
    model.fit(train[FEATURES], train["gross_sales_usd"])
    test["seasonal_naive_usd"] = test["lag_12"]
    test["model_usd"] = model.predict(test[FEATURES]).clip(0)
    actual = test["gross_sales_usd"]
    baseline_errors = summarize_errors(actual, test["seasonal_naive_usd"])
    model_errors = summarize_errors(actual, test["model_usd"])
    winner = "ridge_model" if model_errors["mae_usd"] < baseline_errors["mae_usd"] else "seasonal_naive"

    next_month = last_month + pd.DateOffset(months=1)
    future = panel[["product_category", "sales_channel"]].drop_duplicates().copy()
    future["sales_month"] = next_month
    future["gross_sales_usd"] = float("nan")
    extended = pd.concat([panel, future], ignore_index=True).sort_values(
        ["product_category", "sales_channel", "sales_month"]
    )
    next_rows = add_features(extended)
    next_rows = next_rows[next_rows["sales_month"] == next_month].copy()
    model.fit(history[FEATURES], history["gross_sales_usd"])
    next_rows["seasonal_naive_usd"] = next_rows["lag_12"]
    next_rows["model_usd"] = model.predict(next_rows[FEATURES]).clip(0)
    next_rows["selected_forecast_usd"] = next_rows[
        "model_usd" if winner == "ridge_model" else "seasonal_naive_usd"
    ]

    test["sales_month"] = test["sales_month"].dt.strftime("%Y-%m-%d")
    next_rows["sales_month"] = next_rows["sales_month"].dt.strftime("%Y-%m-%d")
    output_dir.mkdir(parents=True, exist_ok=True)
    test[["sales_month", "product_category", "sales_channel", "gross_sales_usd",
          "seasonal_naive_usd", "model_usd"]].sort_values(
        ["sales_month", "product_category", "sales_channel"]
    ).to_csv(output_dir / "holdout_predictions.csv", index=False, float_format="%.2f")
    next_rows[["sales_month", "product_category", "sales_channel", "seasonal_naive_usd",
               "model_usd", "selected_forecast_usd"]].sort_values(
        ["product_category", "sales_channel"]
    ).to_csv(output_dir / "next_month_forecast.csv", index=False, float_format="%.2f")

    summary = {
        "target": "monthly gross sales USD by product category and sales channel",
        "source": "silver.sales_enriched",
        "last_complete_month": last_month.strftime("%Y-%m-%d"),
        "excluded_partial_month": excluded_month,
        "holdout_start": pd.Timestamp(test_start).strftime("%Y-%m-%d"),
        "holdout_end": last_month.strftime("%Y-%m-%d"),
        "holdout_method": "one-month-ahead predictions using actual prior months; no refit during holdout",
        "baseline": baseline_errors,
        "ridge_model": model_errors,
        "selected_method": winner,
        "next_forecast_month": next_month.strftime("%Y-%m-%d"),
        "note": "Historical fictional data; this is a teaching experiment, not a current sales forecast.",
    }
    (output_dir / "metrics.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> int:
    try:
        summary = run_forecast()
    except (duckdb.Error, OSError, ValueError, KeyError) as error:
        print(f"Forecast failed: {error}")
        return 1
    print(f"Holdout: {summary['holdout_start']} to {summary['holdout_end']}")
    print(f"Seasonal naive MAE: ${summary['baseline']['mae_usd']:,.2f}")
    print(f"Ridge model MAE:    ${summary['ridge_model']['mae_usd']:,.2f}")
    print(f"Selected: {summary['selected_method']}")
    print(f"Forecast month: {summary['next_forecast_month']}")
    print(f"Files written to: {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
