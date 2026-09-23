# Build With Me #1 — Local Retail Data Pipeline

Follow one retail dataset from CSV files to a sales report. The core project
runs on your computer with Python, pandas, DuckDB, and SQL. It needs no API key,
cloud account, database server, or Docker.

```text
Sales + Products + Stores CSVs → Bronze → Silver → Gold → analysis
```

The question: **How do sales and estimated gross profit change by month,
product category, and sales channel?** The [visual project guide](https://amrlasyraf.github.io/build-with-data/)
shows how the data engineering pipeline connects to the optional Power BI
report and a possible later forecasting exercise.

## Follow the Numbered Folders

Run `START_HERE.bat` once, then open these folders in order. Each has a short
README and the files for that step:

| Step | Folder | What you learn |
|---|---|---|
| 01 | [Source data](step_01_data/README.md) | What the three input CSVs contain |
| 02 | [Bronze](step_02_bronze/README.md) | How raw source values are checked and loaded |
| 03 | [Silver](step_03_silver/README.md) | How sales are cleaned and joined |
| 04 | [Gold](step_04_gold/README.md) | How the monthly summary is built |
| 05 | [Explore](step_05_explore/README.md) | How to query the result in DuckDB |

You can stop after folder 05. `add_ons/`, `docs/`, `src/`, and `tests/` support
the project but are not part of the first reading path.

## Download and Run

On Windows, you do not need Git or an existing Python setup to download the
project:

1. On [GitHub](https://github.com/amrlasyraf/build-with-data), select
   **Code → Download ZIP**.
2. Extract the ZIP. Open the extracted folder, not the ZIP itself.
3. Double-click `START_HERE.bat`.

The launcher checks for Python 3.11 or newer. If Python is missing, follow its
instructions to install Python from [python.org](https://www.python.org/downloads/),
enable **Add Python to PATH**, then reopen the launcher. It creates a virtual
environment in `_local/.venv`, installs the packages, and runs Bronze, Silver,
and Gold. The first run needs internet access for package installation.

A successful run creates `_local/output/retail_pipeline.duckdb` and prints row
counts. With the supplied CSVs, expect:

| Table | Rows |
|---|---:|
| `bronze.sales` | 62,884 |
| `silver.sales_enriched` | 62,884 |
| `gold.monthly_sales_summary` | 979 |

`_local` holds generated files and your machine's setup. Git ignores it; it is
not included when someone downloads the repository. Back up personal work in
that folder before deleting it to start over.

## Explore the Result

After the pipeline succeeds, double-click `OPEN_DATA.bat`. It opens the
[DuckDB local UI](https://duckdb.org/docs/current/core_extensions/ui) in your
browser. The first viewer run needs internet access for the UI extension and
browser assets; queries then run locally without an account.

Expand the **retail** database to see `bronze`, `silver`, and `gold`. Select
**Create Notebook**, add a SQL cell, and try these queries one at a time:

```sql
-- Start with the answer table.
SELECT *
FROM retail.gold.monthly_sales_summary
ORDER BY sales_month, product_category, sales_channel
LIMIT 20;

-- Compare the three stages by row count.
SELECT 'Bronze sales' AS layer, count(*) AS rows FROM retail.bronze.sales
UNION ALL
SELECT 'Silver sales', count(*) FROM retail.silver.sales_enriched
UNION ALL
SELECT 'Gold summary', count(*) FROM retail.gold.monthly_sales_summary;

-- Summarize the result by channel.
SELECT sales_channel,
       sum(units_sold) AS units_sold,
       sum(gross_sales_usd) AS gross_sales_usd,
       sum(estimated_gross_profit_usd) AS estimated_gross_profit_usd
FROM retail.gold.monthly_sales_summary
GROUP BY sales_channel
ORDER BY sales_channel;
```

The viewer keeps a read-only connection to the pipeline database. Press Enter
in the `OPEN_DATA.bat` window before rerunning the pipeline; closing only the
browser tab does not release the database lock. If the browser does not open,
visit `http://localhost:4213` while the viewer window is running.

## Trace the Data

The three source files are in `step_01_data/`:

| File | What it contributes |
|---|---|
| `Sales.csv` | Order lines, dates, product and store keys, quantities |
| `Products.csv` | Product names, categories, standard USD prices and costs |
| `Stores.csv` | Store locations; store key `0` represents online sales |

The pipeline uses a local version of the Medallion Architecture. Bronze,
Silver, and Gold are schemas inside one DuckDB file, not separate servers.

| Layer | What to look for | Main table |
|---|---|---|
| Bronze | Source-shaped values, still stored as text | `bronze.sales`, `bronze.products`, `bronze.stores` |
| Silver | Clean dates and numbers, join product and store details, calculate line-level measures | `silver.sales_enriched` |
| Gold | Group lines by month, category, and channel | `gold.monthly_sales_summary` |

Trace a product price through Bronze and Silver:

```sql
SELECT product_key, unit_price_usd, unit_cost_usd
FROM retail.bronze.products
WHERE product_key = '1';

SELECT order_number, product_name, quantity, unit_price_usd,
       gross_sales_usd, estimated_gross_profit_usd
FROM retail.silver.sales_enriched
WHERE product_key = 1
ORDER BY order_number, line_item
LIMIT 10;
```

Silver calculates `gross_sales_usd = quantity × unit_price_usd` and
`estimated_gross_profit_usd = quantity × (unit_price_usd - unit_cost_usd)`.
These are teaching metrics based on standard product price and cost. The source
does not include transaction-level discounts, taxes, refunds, or final
accounting costs, so the profit figure is an estimate.

To see how the stages are implemented, read in this order:

| File | Role |
|---|---|
| `run_pipeline.py` | Runs all stages or selects one |
| `step_02_bronze/source_validation.py` + `bronze.py` | Validates and loads CSV data |
| `step_03_silver/silver.py` + `silver.sql` | Cleans values, joins tables, calculates measures |
| `step_04_gold/gold.py` + `gold.sql` | Aggregates the monthly summary |

Python manages execution and failures; SQL handles relational transformations.
Column definitions and join rules are in [the data model](docs/DATA_MODEL.md).

## Retry One Stage

Run these commands from the extracted project folder. `START_HERE.bat` creates
the Python environment used here:

```powershell
_local\.venv\Scripts\python.exe run_pipeline.py --layer bronze
_local\.venv\Scripts\python.exe run_pipeline.py --layer silver
_local\.venv\Scripts\python.exe run_pipeline.py --layer gold
```

Without `--layer`, the runner executes Bronze → Silver → Gold and stops at the
first failure. Silver needs a committed Bronze table; Gold needs committed
Silver. A Gold retry does not reload the CSVs or rebuild Silver. Each stage
replaces its own output in a transaction, so a failed stage leaves its last
committed result available.

```powershell
_local\.venv\Scripts\python.exe run_pipeline.py
```

This is a full-refresh pipeline. Run one writer at a time. If you change source
data or rebuild an upstream stage, rerun downstream stages in order; they do
not update themselves automatically.

## Optional Add-ons

These are separate from the core pipeline. Their full instructions are in
[Optional Add-ons](docs/ADD_ONS.md).

For data-quality checks, run:

```powershell
_local\.venv\Scripts\python.exe -m add_ons.data_quality.run_checks
```

The checks cover keys, joins, dates, allowed channels, row counts, Gold grain,
and reconciliation. Results are stored in `quality.check_results`; the latest
run is in `quality.latest_check_results`. This add-on does not rebuild any
pipeline stage.

For Power BI, first export Gold as a CSV:

```powershell
_local\.venv\Scripts\python.exe -m add_ons.power_bi.export_gold
```

Open [the sample report](add_ons/power_bi/sales-dashboard.pbix) in Power BI
Desktop. Under **Home → Transform data**, edit the CSV query's **Source** step
to point to your `_local/exports/monthly_sales_summary.csv`, then select
**Close & Apply** and **Refresh**. Save a personal copy in `_local/reports/`.
The report is a downloadable `.pbix`, not a hosted dashboard. PostgreSQL is
not required.

## Reference

### Manual setup with Git

If you prefer the command line, run these commands from PowerShell:

```powershell
git clone https://github.com/amrlasyraf/build-with-data.git
cd build-with-data
python -m venv _local\.venv
_local\.venv\Scripts\python.exe -m pip install -r requirements.txt
_local\.venv\Scripts\python.exe run_pipeline.py
```

### Tests

```powershell
_local\.venv\Scripts\python.exe -m pytest
```

Tests cover source validation, layer retries and failure isolation, joins,
aggregations, data quality, and the Power BI export.

### Dataset and scope

The project uses the fictitious [Global Electronics Retailer dataset](https://mavenanalytics.io/data-playground/global-electronics-retailer)
published by Maven Analytics. Maven lists Microsoft as the source and the
licence as Public Domain. The source field reference is
`docs/Data_Dictionary.csv`.

`step_01_data/optional/Customers.csv` and `Exchange_Rates.csv` are included but not
used by the core pipeline. Prices and costs in `Products.csv` are already in
USD; this project does not claim to convert transaction currencies. A
PostgreSQL version is a possible future extension, not an implemented feature.
Airflow, Spark, Kafka, and cloud deployment are outside Project #1.

### Common problems

| Problem | What to do |
|---|---|
| Python was not found | Install Python 3.11 or newer, enable **Add Python to PATH**, then reopen `START_HERE.bat`. |
| A source CSV was not found | Extract the whole ZIP and keep `START_HERE.bat` alongside `step_01_data/`. |
| Package installation failed | Check the internet connection and run `START_HERE.bat` again. |
| The database is locked | Press Enter in the `OPEN_DATA.bat` window and close other apps using the DuckDB file. |
| Silver or Gold is missing its input | Run the upstream stage first, then retry the failed stage. |
