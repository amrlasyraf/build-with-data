"""Optional preflight checks for the three source CSV files."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from support.pipeline.settings import DATASET_DIR, SOURCE_COLUMNS


class SourceValidationError(ValueError):
    """Raised when a required source file cannot be used safely."""


@dataclass
class SourceSummary:
    """The row and column counts of a checked CSV file."""
    file_name: str
    row_count: int
    column_count: int


def validate_sources(dataset_dir: Path) -> list[SourceSummary]:
    """Report file, encoding, header, and empty-file problems before Bronze."""
    checked_sources: list[SourceSummary] = []

    for file_name, expected_columns in SOURCE_COLUMNS.items():
        file_path = dataset_dir / file_name

        if not file_path.is_file():
            raise SourceValidationError(f"required file not found: {file_path}")

        try:
            dataframe = pd.read_csv(
                file_path,
                encoding="utf-8",
                dtype=str,
                keep_default_na=False,
            )
        except UnicodeDecodeError as error:
            raise SourceValidationError(
                f"{file_name} is not valid UTF-8"
            ) from error
        except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError) as error:
            raise SourceValidationError(
                f"could not read {file_name}: {error}"
            ) from error

        actual_columns = dataframe.columns.tolist()
        if actual_columns != expected_columns:
            missing_columns = [
                column for column in expected_columns if column not in actual_columns
            ]
            unexpected_columns = [
                column for column in actual_columns if column not in expected_columns
            ]
            details = []
            if missing_columns:
                details.append(f"missing columns: {', '.join(missing_columns)}")
            if unexpected_columns:
                details.append(
                    f"unexpected columns: {', '.join(unexpected_columns)}"
                )
            if not details:
                details.append("columns are in a different order")

            raise SourceValidationError(
                f"{file_name} has an unexpected header ({'; '.join(details)})"
            )

        if dataframe.empty:
            raise SourceValidationError(f"{file_name} contains no data rows")

        checked_sources.append(
            SourceSummary(
                file_name=file_name,
                row_count=len(dataframe),
                column_count=len(dataframe.columns),
            )
        )

    return checked_sources


def main() -> int:
    try:
        summaries = validate_sources(DATASET_DIR)
    except SourceValidationError as error:
        print(f"Source check failed: {error}")
        return 1
    for summary in summaries:
        print(f"{summary.file_name}: {summary.row_count:,} rows, {summary.column_count} columns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
