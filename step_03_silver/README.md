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

Reopen the viewer with `-m support.viewer` and compare the source-formatted
price with the numeric Silver result:

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
