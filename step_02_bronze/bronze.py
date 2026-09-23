"""Load validated source data into source-shaped Bronze tables."""

from pathlib import Path

import duckdb

from step_02_bronze.source_validation import ValidatedSource


def load_bronze_tables(
    database_path: Path, sources: list[ValidatedSource]
) -> dict[str, int]:
    """Replace all Bronze tables in one transaction and return row counts."""
    loaded_rows: dict[str, int] = {}

    with duckdb.connect(str(database_path)) as connection:
        connection.execute("BEGIN TRANSACTION")

        try:
            for source in sources:
                temporary_view = f"source_{source.table_name}"
                table_name = f"bronze.{source.table_name}"

                connection.register(temporary_view, source.dataframe)
                try:
                    connection.execute(
                        f"""
                        CREATE OR REPLACE TABLE {table_name} AS
                        SELECT
                            source_data.*,
                            current_timestamp AS loaded_at,
                            ? AS source_file
                        FROM {temporary_view} AS source_data
                        """,
                        [source.file_name],
                    )
                finally:
                    connection.unregister(temporary_view)

                row_count = connection.execute(
                    f"SELECT count(*) FROM {table_name}"
                ).fetchone()[0]

                if row_count != source.row_count:
                    raise RuntimeError(
                        f"{table_name} received {row_count:,} rows; "
                        f"expected {source.row_count:,}"
                    )

                loaded_rows[source.table_name] = row_count

            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise

    return loaded_rows
