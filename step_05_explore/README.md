# 05 — Explore the result

After Bronze, Silver, and Gold finish, double-click `OPEN_DATA.bat` in the
repository root. It starts a local DuckDB viewer. Expand the `retail` database
and run the example queries in [the main README](../README.md#explore-the-result).

`viewer.py` opens the pipeline database read-only and stores the viewer's own
state separately in `_local/output/viewer.duckdb`. Press Enter in the viewer
window before rerunning the pipeline so it can write to the database.

Once you can explain the Gold result, you can try the optional
[data-quality and Power BI add-ons](../docs/ADD_ONS.md).
