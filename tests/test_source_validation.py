from pathlib import Path

import pytest

from src.source_validation import SourceValidationError, validate_sources


VALID_FILES = {
    "Sales.csv": (
        "Order Number,Line Item,Order Date,Delivery Date,CustomerKey,StoreKey,"
        "ProductKey,Quantity,Currency Code\n"
        "1,1,1/1/2024,,10,0,100,2,USD\n"
    ),
    "Products.csv": (
        "ProductKey,Product Name,Brand,Color,Unit Cost USD,Unit Price USD,"
        "SubcategoryKey,Subcategory,CategoryKey,Category\n"
        "100,Example Product,Example Brand,Black,$10.00,$20.00,01,Example,1,Test\n"
    ),
    "Stores.csv": (
        "StoreKey,Country,State,Square Meters,Open Date\n"
        "0,Online,Online,,1/1/2020\n"
    ),
}


def write_sources(directory: Path, files: dict[str, str] = VALID_FILES) -> None:
    for file_name, contents in files.items():
        (directory / file_name).write_text(contents, encoding="utf-8")


def test_validate_sources_returns_row_and_column_counts(tmp_path: Path) -> None:
    write_sources(tmp_path)

    summaries = validate_sources(tmp_path)

    assert [summary.file_name for summary in summaries] == [
        "Sales.csv",
        "Products.csv",
        "Stores.csv",
    ]
    assert [summary.row_count for summary in summaries] == [1, 1, 1]
    assert [summary.column_count for summary in summaries] == [9, 10, 5]


def test_validate_sources_rejects_a_missing_file(tmp_path: Path) -> None:
    incomplete_files = {
        name: contents
        for name, contents in VALID_FILES.items()
        if name != "Stores.csv"
    }
    write_sources(tmp_path, incomplete_files)

    with pytest.raises(SourceValidationError, match="required file not found"):
        validate_sources(tmp_path)


def test_validate_sources_rejects_an_unexpected_header(tmp_path: Path) -> None:
    changed_files = dict(VALID_FILES)
    changed_files["Sales.csv"] = VALID_FILES["Sales.csv"].replace(
        "Currency Code", "Currency"
    )
    write_sources(tmp_path, changed_files)

    with pytest.raises(SourceValidationError, match="unexpected header"):
        validate_sources(tmp_path)
