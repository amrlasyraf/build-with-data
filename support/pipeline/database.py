"""Create the local DuckDB file and Medallion schemas."""

from pathlib import Path

import duckdb

from support.pipeline.settings import MEDALLION_SCHEMAS


def prepare_database(database_path: Path) -> tuple[str, ...]:
    """Create the database and schemas safely on the first or a later run."""
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(database_path)) as connection:
        for schema_name in MEDALLION_SCHEMAS:
            connection.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")

    return MEDALLION_SCHEMAS
