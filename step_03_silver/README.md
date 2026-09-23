# 03 — Silver: clean and join

Silver turns source text into dates and numbers, joins sales to products and
stores, and calculates line-level sales and estimated gross profit. Each row
still represents one product line in an order.

Read `silver.sql` for the transformations, then `silver.py` for the transaction
and checks around them. Sales are joined on `ProductKey` and `StoreKey`. Missing
or duplicate product or store keys cause the stage to fail instead of silently
losing or multiplying sales lines.

Bronze must already be committed. Run only Silver from the repository
root:

```powershell
.\_local\.venv\Scripts\python.exe -m step_00_setup.run_pipeline --layer silver
```

Compare a source-formatted price in `retail.bronze.products` with its numeric
value in `retail.silver.sales_enriched`. The [main README](../README.md)
has a query you can paste into the data viewer.

Next: [04 — Gold](../step_04_gold/README.md).
