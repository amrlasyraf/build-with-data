# 05 — Explore the result

After Bronze, Silver, and Gold finish, start the local DuckDB viewer yourself
from the repository root:

```powershell
.\_local\.venv\Scripts\python.exe -m step_05_explore.viewer
```

Expand the `retail` database
and run the example queries in [the main README](../README.md).

`viewer.py` opens the pipeline database read-only and stores the viewer's own
state separately in `_local/output/viewer.duckdb`. Press Enter in the viewer
window before rerunning the pipeline so it can write to the database.

Once you can explain the Gold result, you can try the optional
[data-quality and Power BI add-ons](../step_06_optional/README.md).
