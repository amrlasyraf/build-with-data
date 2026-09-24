# Build With Me #1 — Local Retail Data Pipeline

Build a retail data pipeline yourself, one layer at a time. You will read three
CSV files, load Bronze, clean and join Silver, aggregate Gold, and query the
result. The project runs locally with Python, pandas, DuckDB, and SQL—no API
key, cloud account, database server, or Docker required.

```text
CSV files → Bronze → Silver → Gold → analysis
```

The question is: **How do sales and estimated gross profit change by month,
product category, and sales channel?** The [visual project guide](https://amrlasyraf.github.io/build-with-data/)
shows where the optional Power BI report fits.

## Follow the folders in order

Each numbered folder has a short README and the files for that step. No step
runs automatically when you download the repository.

| Step | Folder | Your task |
|---|---|---|
| 00 | [Set up](step_00_setup/README.md) | Install Python packages in a project environment |
| 01 | [Source data](step_01_data/README.md) | Inspect the three input CSVs |
| 02 | [Bronze](step_02_bronze/README.md) | Run the source load |
| 03 | [Silver](step_03_silver/README.md) | Run the cleaning and joins |
| 04 | [Gold](step_04_gold/README.md) | Run the monthly aggregation |
| 05 | [Optional](step_05_optional/README.md) | Try deeper data quality, Power BI, or forecasting |

You can stop after Step 04. Inspect the data while completing each layer; it is
not a separate stage. `support/` holds the optional viewer, shared code, tests, and the data
model for a deeper look. `docs/` contains the project website; neither is an
extra step you must complete. The root `README.md` is GitHub's entry page, and
`.gitignore` keeps generated files out of Git.

## 00 — Prepare your computer

These instructions use Windows PowerShell. Start with the
[detailed setup guide](step_00_setup/README.md) if a terminal or virtual
environment is new to you.

| Prerequisite | Required? | Why |
|---|---|---|
| [Python 3.11 or newer](https://www.python.org/downloads/) | Yes | Runs the project |
| Internet connection for first setup | Yes | Downloads the Python packages |
| [VS Code](https://code.visualstudio.com/Download) | Recommended | Helps you browse files and use a terminal |
| [VS Code Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) | Recommended with VS Code | Helps with Python editing; it does not install Python |
| Git | No | Download ZIP works instead |
| Power BI Desktop | No | Only needed for the optional report |

On [GitHub](https://github.com/amrlasyraf/build-with-data), select
**Code → Download ZIP**, extract it, and open the extracted project folder in
VS Code or PowerShell. Run all commands below from that folder—the one with
this README. First check Python, create your environment, and install packages:

```powershell
python --version
python -m venv _local\.venv
.\_local\.venv\Scripts\python.exe -m pip install -r step_00_setup\requirements.txt
```

Check that `python --version` shows 3.11 or newer. If `python` is not found,
try `py -3 --version` and use `py -3` for the environment-creation command.
If neither works, install Python and reopen the terminal. The first package
installation needs internet access. DuckDB installs as a Python package; no
separate database server is needed.

`_local/` holds the environment and generated files. Git ignores this folder,
so it is not part of the public download. Back up personal work saved there
before deleting it to start over.

## 01 — Inspect the CSVs

Open `step_01_data/` and look at the first few rows of these files before
running the pipeline:

| File | What it contains |
|---|---|
| `Sales.csv` | Order lines, dates, product and store keys, quantities |
| `Products.csv` | Product names, categories, standard USD prices and costs |
| `Stores.csv` | Store locations; store key `0` represents online sales |

Find `ProductKey` and `StoreKey` in the sales data. Silver will use them to
join the other two files. `Data_Dictionary.csv` explains the source fields;
it is documentation, not a fourth pipeline input.

## 02 — Load Bronze

Bronze stores source-shaped tables. Values such as dates and prices remain
text so you can compare the original files with their later cleaned versions.
Run the first stage yourself:

```powershell
.\_local\.venv\Scripts\python.exe -m step_00_setup.run_pipeline --layer bronze
```

Expected: 62,884 sales rows, 2,517 products, and 67 stores. The command
creates `_local/output/retail_pipeline.duckdb`.

To inspect Bronze, start the viewer, run a query from the
[Bronze guide](step_02_bronze/README.md), then stop the viewer before running
Silver:

```powershell
.\_local\.venv\Scripts\python.exe -m support.viewer
```

## 03 — Build Silver

Silver converts dates and numbers, joins sales to products and stores, and
calculates line-level sales and estimated gross profit. It needs Bronze to
have succeeded first.

```powershell
.\_local\.venv\Scripts\python.exe -m step_00_setup.run_pipeline --layer silver
```

Expected: 62,884 rows in `silver.sales_enriched`. Read
`step_03_silver/silver.sql` to see the cleaning and joins. Reopen the viewer
and compare Bronze and Silver using the [Silver guide](step_03_silver/README.md).

## 04 — Build Gold

Gold groups Silver sales by month, product category, and sales channel. It
needs Silver to have succeeded first.

```powershell
.\_local\.venv\Scripts\python.exe -m step_00_setup.run_pipeline --layer gold
```

Expected: 979 rows in `gold.monthly_sales_summary`. The measures are based on
standard product prices and costs:

```text
gross_sales_usd = quantity × unit_price_usd
estimated_gross_profit_usd = quantity × (unit_price_usd - unit_cost_usd)
```

This is **estimated** gross profit, not accounting profit. The source has no
transaction-level discounts, taxes, refunds, or final accounting costs.

Reopen the viewer and answer the project question with the query in the
[Gold guide](step_04_gold/README.md). Exploration is part of each layer, not
another pipeline step.

Each stage replaces only its own table in a transaction. If Gold fails, you
can retry the Gold command without reloading Bronze or rebuilding Silver. A
failed stage leaves its previous committed result available. After changing
upstream data, rerun the affected downstream stages in order; this local
pipeline does not update them automatically. Run only one writer at a time.

## Explore while you build

Start the local DuckDB viewer yourself:

```powershell
.\_local\.venv\Scripts\python.exe -m support.viewer
```

The first viewer run needs internet access for the DuckDB UI extension and
browser assets. Queries run locally without an account. In the browser,
expand the **retail** database, select **Create Notebook**, add a SQL cell,
and try these queries one at a time:

```sql
-- Look at the analytics-ready result.
SELECT *
FROM retail.gold.monthly_sales_summary
ORDER BY sales_month, product_category, sales_channel
LIMIT 20;

-- Compare row counts across the layers.
SELECT 'Bronze sales' AS layer, count(*) AS rows FROM retail.bronze.sales
UNION ALL
SELECT 'Silver sales', count(*) FROM retail.silver.sales_enriched
UNION ALL
SELECT 'Gold summary', count(*) FROM retail.gold.monthly_sales_summary;

-- Compare results by sales channel.
SELECT sales_channel,
       sum(units_sold) AS units_sold,
       sum(gross_sales_usd) AS gross_sales_usd,
       sum(estimated_gross_profit_usd) AS estimated_gross_profit_usd
FROM retail.gold.monthly_sales_summary
GROUP BY sales_channel
ORDER BY sales_channel;
```

To compare a source-formatted product price with Silver's numeric value:

```sql
SELECT product_key, unit_price_usd FROM retail.bronze.products
WHERE product_key = '1';

SELECT order_number, product_name, quantity, unit_price_usd, gross_sales_usd
FROM retail.silver.sales_enriched
WHERE product_key = 1
ORDER BY order_number, line_item
LIMIT 10;
```

Press Enter in the viewer's terminal to stop it before rerunning a pipeline
stage. Closing only the browser tab does not release the database lock. If the
browser does not open, visit `http://localhost:4213` while the viewer runs.

## 05 — Optional exercises

The core pipeline is complete after Step 04. [Step 05](step_05_optional/README.md)
explains deeper data-quality checks, the Power BI export/report, and a
Silver-based forecasting experiment. None is required for Bronze, Silver, or
Gold. PostgreSQL is not implemented.

## Reference

The pipeline runner is `step_00_setup/run_pipeline.py`. Python controls each
stage and its failures; SQL in the Silver and Gold folders handles joins and
aggregation. [The data model](support/DATA_MODEL.md) lists columns, row grain,
and join rules.

The data comes from Maven Analytics' fictitious
[Global Electronics Retailer dataset](https://mavenanalytics.io/data-playground/global-electronics-retailer).
Maven lists Microsoft as the source and the licence as Public Domain.
`step_01_data/optional/Customers.csv` and `Exchange_Rates.csv` are included
but not loaded. Product price and cost are already in USD; this project does
not claim to convert the transaction currency.

If you already use Git, `git clone https://github.com/amrlasyraf/build-with-data.git`
can replace Download ZIP. The setup and run commands stay the same.

Run the optional automated tests after installing packages:

```powershell
.\_local\.venv\Scripts\python.exe -m pytest support/tests
```

| Problem | What to check |
|---|---|
| Python is not found or is too old | Install Python 3.11 or newer, reopen the terminal, and check `python --version` or `py -3 --version`. |
| The virtual-environment command fails | Confirm you are in the extracted project folder and Python is installed. |
| A source CSV is missing | Extract the entire ZIP, including `step_01_data/`. |
| A package is missing | Rerun the `pip install -r step_00_setup\requirements.txt` command with the `_local` Python executable. |
| Silver or Gold has no input | Run the preceding stage first. |
| The database is locked | Stop the viewer with Enter and close other programs using the DuckDB file. |
