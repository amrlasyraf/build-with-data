# 04 — Gold: answer the question

Gold groups Silver sales lines by month, product category, and sales channel.
Its output, `gold.monthly_sales_summary`, is the table used for analysis and
the optional Power BI report.

Read `gold.sql` to see the grouping and sums. Read `gold.py` to see how Gold
runs in its own transaction. A Gold retry does not reload the CSVs or rebuild
Bronze and Silver.

Silver must already be committed. Run only Gold from the repository root:

```powershell
.\_local\.venv\Scripts\python.exe -m step_00_setup.run_pipeline --layer gold
```

Gross profit is **estimated** from standard product prices and costs. The
source does not supply discounts, refunds, tax, or final accounting profit.

Reopen the viewer with `-m support.viewer` and inspect the monthly result:

```sql
SELECT sales_month, product_category, sales_channel,
       gross_sales_usd, estimated_gross_profit_usd
FROM retail.gold.monthly_sales_summary
ORDER BY sales_month, product_category, sales_channel
LIMIT 20;
```

The core project is complete here. If you want more, choose an
[optional exercise](../step_05_optional/README.md).
