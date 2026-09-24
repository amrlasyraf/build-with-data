# Support files

The numbered folders are the learning path. This folder is for readers who
want to inspect the shared pieces used by several steps:

- `pipeline/` holds paths, source column names, database setup, and checks for
  committed upstream tables.
- `viewer.py` opens the DuckDB UI to inspect each layer while you build it.
- `tests/` checks that loading, transformations, retries, data quality, and
  optional exercises work as expected.
- `DATA_MODEL.md` lists the tables, their row grain, columns, and join rules.

You do not need to read this folder to run the project. For the guided path,
start with [Step 00 — Setup](../step_00_setup/README.md).
