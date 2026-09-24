# 02 — Bronze: load the source

Bronze stores the three CSVs in DuckDB with source values still represented as
text. This makes it possible to compare what arrived with what Silver later
cleans. The loader adds a timestamp and source filename to each row.

Read `bronze.py` to see how pandas reads the CSVs and replaces all three
tables in one transaction. A file that cannot be loaded stops the stage;
the previous committed tables remain. Explicit checks for file presence,
headers, UTF-8 encoding, and empty sources are an
[optional exercise in Step 05](../step_05_optional/README.md).

After completing Step 00, open `step_02_bronze/bronze.py` in VS Code and click
**Run Python File** at the top right. The output should show 62,884 sales,
2,517 products, and 67 stores. Bronze creates the local DuckDB file under
`_local/output/`.

To inspect Bronze, open `support/viewer.py` in VS Code and click **Run Python
File**. When the browser opens, expand the `retail` database and try this
query:

```sql
SELECT order_number, order_date, product_key, store_key, quantity
FROM retail.bronze.sales
ORDER BY order_number, line_item
LIMIT 10;
```

Press Enter in the VS Code panel opened by Run Python File to stop the viewer
before running Silver.
Closing only the browser tab does not release the database connection.

Next: [03 — Silver](../step_03_silver/README.md).
