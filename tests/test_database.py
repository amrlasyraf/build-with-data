from pathlib import Path

import duckdb

from src.database import prepare_database


def test_prepare_database_creates_medallion_schemas(tmp_path: Path) -> None:
    database_path = tmp_path / "retail_pipeline.duckdb"

    prepare_database(database_path)
    prepare_database(database_path)

    with duckdb.connect(str(database_path), read_only=True) as connection:
        schema_names = {
            row[0]
            for row in connection.execute(
                """
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name IN ('bronze', 'silver', 'gold')
                """
            ).fetchall()
        }

    assert schema_names == {"bronze", "silver", "gold"}
