# Optional Add-ons

The core project ends with a working local DuckDB pipeline and a queryable Gold
table. These add-ons are optional. Start with the core pipeline; return here
when you want to explore data quality or Power BI.

## Add-on 1 — Data Quality

**Status: implemented.** Run it after the core pipeline:

```powershell
_local\.venv\Scripts\python.exe -m add_ons.data_quality.run_checks
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

## Add-on 2 — PostgreSQL

**Status: not implemented.** The repository does not include a PostgreSQL
pipeline or setup guide. This is a possible follow-up project, not a step needed
for the DuckDB pipeline or Power BI report.

### Purpose

Introduce the difference between an embedded database and a client/server
database after the learner already understands the pipeline itself.

### Learning goals

- install or run PostgreSQL locally
- understand host, port, database, username, and password
- keep credentials in environment variables
- recreate the Bronze, Silver, and Gold schemas
- load the same three sources and reproduce the same Gold result
- inspect tables with pgAdmin or DBeaver

These are topics for a future implementation; the commands in this repository
continue to use DuckDB.

## Add-on 3 — Power BI

**Status: Gold CSV export and sample Power BI report available.** Create the
file after running the core pipeline:

```powershell
_local\.venv\Scripts\python.exe -m add_ons.power_bi.export_gold
```

The command writes `_local/exports/monthly_sales_summary.csv`. It replaces the
previous export, preserves a stable row order, and leaves the DuckDB tables
unchanged.

### Purpose

Show how an analytics tool consumes the Gold layer rather than rebuilding the
pipeline logic inside a dashboard.

### Beginner path

1. Complete the core pipeline using `START_HERE.bat`.
2. Run the Gold CSV export command above.
3. Open [the sample report](../add_ons/power_bi/sales-dashboard.pbix) in Power
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

## Later Projects, Not Add-ons

Spark, Kafka, workflow orchestration, and cloud deployment are outside this
local project. They introduce infrastructure beyond the pipeline covered here.
