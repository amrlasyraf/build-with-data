"""Check the same file-by-file path used by VS Code's Run Python File button."""

from decimal import Decimal
from pathlib import Path
import shutil
import subprocess
import sys

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_layer_files_run_directly_from_another_working_directory(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    for folder in ("step_02_bronze", "step_03_silver", "step_04_gold", "support"):
        shutil.copytree(
            PROJECT_ROOT / folder,
            project / folder,
            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"),
        )

    data = project / "step_01_data"
    data.mkdir()
    (data / "Sales.csv").write_text(
        "Order Number,Line Item,Order Date,Delivery Date,CustomerKey,StoreKey,"
        "ProductKey,Quantity,Currency Code\n1,1,1/1/2024,,10,0,100,2,USD\n",
        encoding="utf-8",
    )
    (data / "Products.csv").write_text(
        "ProductKey,Product Name,Brand,Color,Unit Cost USD,Unit Price USD,"
        "SubcategoryKey,Subcategory,CategoryKey,Category\n"
        "100,Example Product,Example Brand,Black,$10.00,$20.00,01,Example,1,Test\n",
        encoding="utf-8",
    )
    (data / "Stores.csv").write_text(
        "StoreKey,Country,State,Square Meters,Open Date\n"
        "0,Online,Online,,1/1/2020\n",
        encoding="utf-8",
    )

    def run_file(relative_path: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(project / relative_path)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )

    before_bronze = run_file("step_03_silver/silver.py")
    assert before_bronze.returncode == 1
    assert "Run bronze.py first" in before_bronze.stdout

    viewer_before_bronze = run_file("support/viewer.py")
    assert viewer_before_bronze.returncode == 1
    assert "Database not found. Run Bronze first" in viewer_before_bronze.stdout

    for script, expected in (
        ("step_02_bronze/bronze.py", "Bronze sales: 1 rows"),
        ("step_03_silver/silver.py", "Silver complete: 1 rows"),
        ("step_04_gold/gold.py", "Gold complete: 1 rows"),
    ):
        result = run_file(script)
        assert result.returncode == 0, result.stdout + result.stderr
        assert expected in result.stdout

    with duckdb.connect(str(project / "_local/output/retail_pipeline.duckdb"), read_only=True) as connection:
        assert connection.execute(
            "SELECT units_sold, gross_sales_usd, estimated_gross_profit_usd "
            "FROM gold.monthly_sales_summary"
        ).fetchone() == (2, Decimal("40.00"), Decimal("20.00"))
