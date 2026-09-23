# Build With Me #1 — Local Retail Data Pipeline

Build a production-style batch pipeline on your own computer:

```text
CSV files → Bronze → Silver → Gold → SQL analysis
```

The pipeline uses Python and pandas for source validation, DuckDB for local
storage, and SQL for transformations. It runs without a cloud account, database
server, Docker, or API key.

The business question is:

> How do sales and estimated gross profit change by month, product category,
> and sales channel?

## Three Files to Know

If this is your first data pipeline, start with only these files:

| File | When to use it |
|---|---|
| `START_HERE.bat` | Set up the project and run the complete pipeline |
| `OPEN_DATA.bat` | Open the finished Bronze, Silver, and Gold tables |
| `README.md` | Follow the walkthrough and copy the example queries |

The other folders contain the pipeline implementation, tests, documentation,
and optional advanced work. You do not need to understand all of them before
running the project.

## Start Here on Windows

You do not need Git or previous GitHub experience.

1. On the GitHub page, select the green **Code** button.
2. Select **Download ZIP**.
3. Open Downloads, right-click the ZIP, and select **Extract All**.
4. Open the extracted project folder. Do not run it from inside the ZIP.
5. Double-click **START_HERE.bat**.

The launcher checks for Python 3.11 or newer, creates a private environment
under `_local`, installs the project packages, and runs the complete pipeline.
The first run needs an internet connection to install packages.

If Python is missing, the launcher explains how to install it from
[python.org](https://www.python.org/downloads/). Enable **Add Python to PATH**
during installation, close the launcher window, and run it again.

A successful run ends with committed row counts for all three layers and creates:

```text
_local\output\retail_pipeline.duckdb
```

`_local` contains machine-specific files such as the Python environment and
generated databases. Git ignores the whole folder, so none of it is published.
Delete `_local` whenever you want to reset the project completely.

With the supplied data, expect:

| Output | Rows |
|---|---:|
| `bronze.sales` | 62,884 |
| `silver.sales_enriched` | 62,884 |
| `gold.monthly_sales_summary` | 979 |

## What the Pipeline Does

```text
Sales.csv ─────┐
Products.csv ──┼─→ pandas validation → bronze tables
Stores.csv ────┘                           │
                                            ▼
                               silver.sales_enriched
                               clean types + two joins
                                            │
                                            ▼
                            gold.monthly_sales_summary
                         month + category + sales channel
```

Each layer is an independent task with its own transaction:

| Layer | Responsibility | Main output |
|---|---|---|
| Bronze | Load validated source files without hiding source formatting | Three source-shaped tables |
| Silver | Type, clean, join, and calculate line-level measures | `silver.sales_enriched` |
| Gold | Aggregate Silver for the business question | `gold.monthly_sales_summary` |

Bronze keeps source values as text, including date strings and dollar signs.
Silver converts dates and numbers, joins products and stores, labels store key
`0` as `Online`, and calculates:

```text
gross_sales_usd = quantity × unit_price_usd
estimated_gross_profit_usd = quantity × (unit_price_usd - unit_cost_usd)
```

Gold groups those sales lines by month, product category, and sales channel.
The profit measure is an estimate based on standard product price and cost. The
source has no transaction-level discounts, taxes, refunds, or accounting costs.

## Explore the Result

After the pipeline succeeds, double-click **OPEN_DATA.bat**. It opens the
[DuckDB local UI](https://duckdb.org/docs/current/core_extensions/ui) in your
browser. The first viewer run needs internet access for the UI extension and
browser assets. Queries run locally and no account is required.

In the browser:

1. Expand the **retail** database to see `bronze`, `silver`, and `gold`.
2. Select **Create Notebook** beside Notebooks.
3. Name it, select **Add Cell**, and paste one query below.
4. Select **Run** on the SQL cell.

The UI may restore notebooks from earlier sessions. Create a new notebook so
you do not accidentally run an unrelated saved query.

```sql
-- Compare source-formatted prices with their cleaned Silver values.
SELECT product_key, unit_price_usd, unit_cost_usd
FROM retail.bronze.products
WHERE product_key = '1';

SELECT order_number, product_name, quantity, unit_price_usd,
       gross_sales_usd, estimated_gross_profit_usd
FROM retail.silver.sales_enriched
WHERE product_key = 1
ORDER BY order_number, line_item
LIMIT 10;

-- Inspect the analytics-ready result.
SELECT *
FROM retail.gold.monthly_sales_summary
ORDER BY sales_month, product_category, sales_channel
LIMIT 20;

-- Reconcile row counts between the layers.
SELECT 'Bronze sales' AS layer, count(*) AS rows FROM retail.bronze.sales
UNION ALL
SELECT 'Silver sales', count(*) FROM retail.silver.sales_enriched
UNION ALL
SELECT 'Gold summary', count(*) FROM retail.gold.monthly_sales_summary;

-- Compare total results by sales channel.
SELECT sales_channel,
       sum(units_sold) AS units_sold,
       sum(gross_sales_usd) AS gross_sales_usd,
       sum(estimated_gross_profit_usd) AS estimated_gross_profit_usd
FROM retail.gold.monthly_sales_summary
GROUP BY sales_channel
ORDER BY sales_channel;
```

The viewer attaches the pipeline database as read-only and stores its own state
in `_local/output/viewer.duckdb`. Press Enter in the viewer window before
rerunning the pipeline. Closing only the browser tab does not release the
database lock.

If the browser does not open automatically, visit `http://localhost:4213` while
the viewer window is running.

## Run and Retry Like an Orchestrator

Running the command without an option executes Bronze → Silver → Gold and stops
at the first failure:

```powershell
python run_pipeline.py
```

Every layer can also run independently:

```powershell
python run_pipeline.py --layer bronze
python run_pipeline.py --layer silver
python run_pipeline.py --layer gold
```

Silver requires committed Bronze tables. Gold requires committed Silver. A Gold
retry does not read the CSVs or rebuild Bronze and Silver. If Gold fails, its
previous committed table remains available while Silver stays unchanged.

This is the dependency chain a future orchestrator could execute:

```text
bronze >> silver >> gold
```

The local project uses full refreshes. Run one pipeline writer at a time. After
changing upstream data, rebuild the affected downstream layers in order. Existing
downstream tables keep their previous version until their own stage succeeds.

## Follow the Implementation

Start with these files:

| File | Purpose |
|---|---|
| `run_pipeline.py` | Selects one layer or runs the complete dependency chain |
| `src/bronze.py` | Loads pandas DataFrames into Bronze in one transaction |
| `src/silver.py` | Runs Silver SQL and validates the joins before commit |
| `sql/01_silver.sql` | Contains the type cleaning, joins, and calculations |
| `src/gold.py` | Runs and validates the Gold task independently |
| `sql/02_gold.sql` | Contains the monthly aggregation |

Python controls execution and failures. SQL owns relational transformations.
This keeps the stage boundaries visible and lets an orchestrator retry one task.

Detailed column contracts are documented in
[docs/DATA_MODEL.md](docs/DATA_MODEL.md).

## Dataset

The project uses the **Global Electronics Retailer** dataset published by Maven
Analytics. It contains fictitious retail transactions and related product,
customer, store, and exchange-rate tables. Maven lists Microsoft as the source
and the dataset licence as Public Domain.

- [Dataset page](https://mavenanalytics.io/data-playground/global-electronics-retailer)
- Core pipeline files: `Sales.csv`, `Products.csv`, and `Stores.csv`
- Optional future files: `Customers.csv` and `Exchange_Rates.csv`
- Source field reference: `docs/Data_Dictionary.csv`

Customers and exchange rates are excluded from the core question. Product prices
and costs are already supplied in USD, so this version does not claim to convert
the transaction currency.

## Manual Setup and Git

If you already use Git, clone the repository instead of downloading the ZIP:

```powershell
git clone https://github.com/amrlasyraf/build-with-data.git
cd build-with-data
```

Manual setup from the project folder:

```powershell
python -m venv _local\.venv
_local\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run_pipeline.py
```

## Tests

The tests cover source validation, Bronze replacement, Silver calculations and
join failures, Gold failure isolation and retries, missing dependencies, and
runner stop behaviour.

```powershell
python -m pytest
```

## Advanced: Run Data-Quality Checks

Complete the core pipeline first, then run the optional quality suite:

```powershell
python -m add_ons.data_quality.run_checks
```

It checks the committed Bronze, Silver, and Gold tables without rebuilding them.
The checks cover non-empty tables, key uniqueness, broken product/store joins,
positive quantities, delivery dates, allowed sales channels, Silver row-count
preservation, required monetary values, Gold grain, and Gold-to-Silver totals.

Every run appends its results to `quality.check_results`. The latest run is
available through `quality.latest_check_results`. A failed rule is saved with
its affected-row count and rate, printed in the terminal, and returns exit code
1 for a future orchestrator.

```sql
SELECT run_id, checked_at, severity, layer, check_name, status,
       failed_rows, total_rows, failure_rate, description
FROM retail.quality.latest_check_results
ORDER BY status, severity, layer, check_name;
```

The DQ suite is an advanced add-on because it introduces test severity,
historical check results, and operational failure handling. The correctness
rules themselves remain production-relevant.

## Common Problems

### Python was not found

Install Python 3.11 or newer from [python.org](https://www.python.org/downloads/),
enable **Add Python to PATH**, then close and reopen the launcher.

### A source CSV was not found

Extract the complete ZIP and keep `START_HERE.bat` in the project folder. Check
that these files exist:

```text
Dataset\Sales.csv
Dataset\Products.csv
Dataset\Stores.csv
```

### Package installation failed

Check your internet connection and run `START_HERE.bat` again. Packages install
only inside this project's `_local\.venv` folder.

### The database is locked

Press Enter in the `OPEN_DATA.bat` window and close any other application using
the DuckDB file. Then rerun the pipeline.

### Silver or Gold reports missing upstream tables

Run the required upstream layer shown in the error message, then retry the failed
layer. For example, run Bronze before Silver and Silver before Gold.

## Scope and Extensions

The core stays local and focused. Optional extensions are described in
[docs/ADD_ONS.md](docs/ADD_ONS.md):

- data-quality checks and historical results (implemented)
- PostgreSQL as a client/server destination
- Power BI using Gold data

Workflow orchestration, Spark, Kafka, and cloud deployment belong in later Build
With Me projects. They add infrastructure and execution concepts beyond this
pipeline's learning goal.
