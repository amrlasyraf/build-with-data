# Optional Add-ons

The core project ends with a working local DuckDB pipeline and a queryable Gold
table. Everything in this document is optional and should be attempted only
after the learner can run and explain the core pipeline.

Add-ons must not change the core command or become prerequisites for it.

## Add-on 1 — Data Quality

**Status: implemented.** Run it after the core pipeline:

```powershell
python -m add_ons.data_quality.run_checks
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

The PostgreSQL version should reuse the same data model and SQL where practical.
Docker may be offered as an alternative setup, but must not be the only path.

## Add-on 3 — Power BI

### Purpose

Show how an analytics tool consumes the Gold layer rather than rebuilding the
pipeline logic inside a dashboard.

### Preferred path

1. Complete the PostgreSQL add-on
2. Connect Power BI to PostgreSQL
3. Import `gold.monthly_sales_summary`
4. Build a minimal report for monthly sales, estimated gross profit, category,
   and channel

For learners who do not want PostgreSQL, the core pipeline may export the Gold
table to CSV as a simpler Power BI input.

## Later Projects, Not Add-ons

Spark, Kafka, workflow orchestration, and cloud deployment introduce enough new
concepts to deserve separate Build With Me projects. They should not be attached
to Project #1 merely to expand its technology list.
