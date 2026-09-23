# 02 — Bronze: load the source

Bronze stores the three CSVs in DuckDB with source values still represented as
text. This makes it possible to compare what arrived with what Silver later
cleans. The loader adds a timestamp and source filename to each row.

Read `source_validation.py` to see how the files, headers, and UTF-8 encoding
are checked. Then read `bronze.py` to see how all three tables are replaced in
one transaction. If the stage fails, its previous committed tables remain.

After completing Step 00, run Bronze from the repository root:

```powershell
.\_local\.venv\Scripts\python.exe -m step_00_setup.run_pipeline --layer bronze
```

After completing Gold, use the viewer in Step 05 to inspect
`retail.bronze.sales`, `retail.bronze.products`, and `retail.bronze.stores`.

Next: [03 — Silver](../step_03_silver/README.md).
