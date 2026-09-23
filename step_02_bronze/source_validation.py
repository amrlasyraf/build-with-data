"""Validate the CSV inputs before the pipeline creates database tables."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.settings import BRONZE_COLUMN_NAMES, BRONZE_TABLE_NAMES, SOURCE_COLUMNS


class SourceValidationError(ValueError):
    """Raised when a required source file cannot be used safely."""


@dataclass
class ValidatedSource:
    """A validated source ready to load into its Bronze table."""

    file_name: str
    table_name: str
    dataframe: pd.DataFrame

    @property
    def row_count(self) -> int:
        return len(self.dataframe)

    @property
    def column_count(self) -> int:
        return len(self.dataframe.columns)


def validate_sources(dataset_dir: Path) -> list[ValidatedSource]:
    """Read and validate the UTF-8 files needed by the core pipeline."""
    validated_sources: list[ValidatedSource] = []

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
        except (OSError, pd.errors.ParserError) as error:
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

        dataframe.columns = BRONZE_COLUMN_NAMES[file_name]

        validated_sources.append(
            ValidatedSource(
                file_name=file_name,
                table_name=BRONZE_TABLE_NAMES[file_name],
                dataframe=dataframe,
            )
        )

    return validated_sources
