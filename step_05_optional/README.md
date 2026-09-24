# 05 — Optional: data quality, Power BI, and forecasting

The core project ends with a working local DuckDB pipeline and a queryable Gold
table. These add-ons are optional. Start with the core pipeline; return here
when you want to explore data quality, Power BI, or forecasting.

## 1. Check Data Quality

**Status: implemented.** Run it after the core pipeline:

```powershell
.\_local\.venv\Scripts\python.exe -m step_05_optional.data_quality.run_checks
```

### Purpose

Show how a pipeline can prove that its output is trustworthy, without mixing a
large set of validation rules into the beginner walkthrough.

### Checks included

- required Bronze, Silver, and Gold tables contain rows
- `(order_number, line_item)` is unique in Bronze sales
- `product_key` is unique in Bronze products
- `store_key` is unique in Bronze stores
- every sales product key joins to a product
- every sales store key joins to a store
- quantity is greater than zero
- delivery date is not earlier than order date when present
- online sales have a delivery date
- Silver row count matches Bronze sales row count
- calculated monetary values are not null
- Silver sales channels contain only the expected values
- Gold contains one row per month, category, and sales channel
- Gold units, sales, and estimated profit reconcile to Silver

The add-on stores append-only results in `quality.check_results`, including the
run identifier, timestamp, layer, severity, status, failing-row count, total-row
count, failure rate, and rule description. `quality.latest_check_results`
exposes the newest run. Any failed rule produces exit code 1. The add-on uses
plain SQL and Python and adds no data-quality framework dependency.

## 2. Open the Power BI Report

**Status: Gold CSV export and Power BI report complete.** Create the
file after running the core pipeline:

```powershell
.\_local\.venv\Scripts\python.exe -m step_05_optional.power_bi.export_gold
```

The command writes `_local/exports/monthly_sales_summary.csv`. It replaces the
previous export, preserves a stable row order, and leaves the DuckDB tables
unchanged.

### Purpose

Show how an analytics tool consumes the Gold layer rather than rebuilding the
pipeline logic inside a dashboard.

### Beginner path

1. Complete Steps 00–04 by running Bronze, Silver, and Gold yourself.
2. Run the Gold CSV export command above.
3. Open [the completed report](power_bi/sales-dashboard.pbix) in Power
   BI Desktop.
4. Under **Home > Transform data**, select the `monthly_sales_summary` query
   and edit its **Source** step to use your own
   `_local/exports/monthly_sales_summary.csv`.
5. Select **Close & Apply**, then **Refresh**. Inspect or change the visuals.

The `.pbix` provides a report layout, but its saved CSV path may not work on
another computer. Save personal edits under `_local/reports/`; that folder is
not included in the repository.

The Power BI report uses the CSV export. No PostgreSQL connection is needed or
included in this version.

## 3. Try a Sales Forecast

**Status: implemented as a local teaching experiment.** It reads cleaned
Silver transactions and does not change the Bronze, Silver, or Gold tables.
See the [forecasting guide](forecasting/README.md) for the assumptions and
limitations. Install its one extra package, then run it from the repository
root:

```powershell
.\_local\.venv\Scripts\python.exe -m pip install -r step_05_optional\forecasting\requirements.txt
.\_local\.venv\Scripts\python.exe -m step_05_optional.forecasting.run_forecast
```

The experiment writes a 12-month backtest, a next-month forecast, and a metric
summary under `_local/forecasts/`. These files are local to your computer.

## Future Idea: PostgreSQL

**Not implemented.** A later version could reproduce the Bronze, Silver, and
Gold tables in PostgreSQL to show how a client/server database differs from
DuckDB. This repository does not contain a PostgreSQL pipeline or setup guide.

## Outside This Project

Spark, Kafka, workflow orchestration, and cloud deployment are outside this
local project. They introduce infrastructure beyond the pipeline covered here.
