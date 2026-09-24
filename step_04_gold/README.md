# 04 — Gold: answer the question

Gold groups Silver sales lines by month, product category, and sales channel.
Its output, `gold.monthly_sales_summary`, is the table used for analysis and
the optional Power BI report.

Read `gold.py` to see the pandas monthly grouping and sums, followed by the
transaction that saves Gold in DuckDB. A Gold retry does not reload the CSVs
or rebuild Bronze and Silver.

Gold reads the committed Silver table, so run Silver first. Then open
`step_04_gold/gold.py` in VS Code and click **Run Python File**. The output
should show 979 rows in `gold.monthly_sales_summary`.

Gross profit is **estimated** from standard product prices and costs. The
source does not supply discounts, refunds, tax, or final accounting profit.

To inspect the monthly result, open `support/viewer.py` in VS Code and click
**Run Python File** again.

Then run this query in the viewer:

```sql
SELECT sales_month, product_category, sales_channel,
       gross_sales_usd, estimated_gross_profit_usd
FROM retail.gold.monthly_sales_summary
ORDER BY sales_month, product_category, sales_channel
LIMIT 20;
```

Gold completes the core pipeline. The
[optional exercises](../step_05_optional/README.md) build on these results.
