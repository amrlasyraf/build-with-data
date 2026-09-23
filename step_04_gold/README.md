# 04 — Gold: answer the question

Gold groups Silver sales lines by month, product category, and sales channel.
Its output, `gold.monthly_sales_summary`, is the table used for analysis and
the optional Power BI report.

Read `gold.sql` to see the grouping and sums. Read `gold.py` to see how Gold
runs in its own transaction. A Gold retry does not reload the CSVs or rebuild
Bronze and Silver.

Silver must already be committed. To retry only Gold from the repository root:

```powershell
_local\.venv\Scripts\python.exe run_pipeline.py --layer gold
```

Gross profit is **estimated** from standard product prices and costs. The
source does not supply discounts, refunds, tax, or final accounting profit.

Next: [05 — Explore](../step_05_explore/README.md).
