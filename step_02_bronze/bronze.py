"""Read the three CSVs with pandas and store source-shaped Bronze tables."""

from dataclasses import dataclass
from pathlib import Path
import sys

# VS Code's Run button starts this file directly, outside the project package.
if __name__ == "__main__" and not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb
import pandas as pd

from support.pipeline.settings import BRONZE_COLUMN_NAMES, BRONZE_TABLE_NAMES, SOURCE_COLUMNS
from support.pipeline.database import prepare_database
from support.pipeline.settings import DATASET_DIR, DATABASE_PATH


@dataclass
class SourceFile:
    file_name: str
    table_name: str
    dataframe: pd.DataFrame

    @property
    def row_count(self) -> int:
        return len(self.dataframe)


def read_sources(dataset_dir: Path) -> list[SourceFile]:
    """Read source files; detailed preflight checks are an optional exercise."""
    sources = []
    for file_name in SOURCE_COLUMNS:
        frame = pd.read_csv(
            dataset_dir / file_name, encoding="utf-8", dtype=str, keep_default_na=False
        )
        # Keep only the fields Bronze uses, in the documented order.
        frame = frame.rename(columns=dict(zip(SOURCE_COLUMNS[file_name], BRONZE_COLUMN_NAMES[file_name])))
        frame = frame[BRONZE_COLUMN_NAMES[file_name]]
        sources.append(SourceFile(file_name, BRONZE_TABLE_NAMES[file_name], frame))
    return sources


def load_bronze_tables(
    database_path: Path, sources: list[SourceFile]
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


def main() -> int:
    """Load Bronze when this file is run from VS Code."""
    try:
        sources = read_sources(DATASET_DIR)
        prepare_database(DATABASE_PATH)
        counts = load_bronze_tables(DATABASE_PATH, sources)
    except (duckdb.Error, ValueError, OSError, RuntimeError, KeyError) as error:
        print(f"Bronze failed: {error}")
        return 1
    for table, count in counts.items():
        print(f"Bronze {table}: {count:,} rows")
    print(f"Bronze complete. Database: {DATABASE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
