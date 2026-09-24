# 03 — Silver: clean and join

Silver turns source text into dates and numbers, joins sales to products and
stores, and calculates line-level sales and estimated gross profit. Each row
still represents one product line in an order.

Read `silver.py` for the pandas date and number conversions, `merge` joins,
calculated values, and the transaction that saves the result in DuckDB. Sales
are joined on `ProductKey` and `StoreKey`. Missing or duplicate product or
store keys cause the stage to fail instead of silently losing or multiplying
sales lines.

Silver reads the committed Bronze tables, so run Bronze first. Then open
`step_03_silver/silver.py` in VS Code and click **Run Python File**. The output
should show 62,884 rows in `silver.sales_enriched`.

To compare the source-formatted price with the numeric Silver result, open
`support/viewer.py` in VS Code and click **Run Python File** again.

Then run these queries in the viewer:

```sql
SELECT product_key, unit_price_usd
FROM retail.bronze.products
WHERE product_key = '1';

SELECT order_number, product_name, quantity, unit_price_usd, gross_sales_usd
FROM retail.silver.sales_enriched
WHERE product_key = 1
ORDER BY order_number, line_item
LIMIT 10;
```

Stop the viewer before running Gold.

Next: [04 — Gold](../step_04_gold/README.md).
