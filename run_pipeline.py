"""Run the local retail data pipeline.

Validate source files, load Bronze, and build Silver and Gold with SQL.
"""

import argparse
import logging

import duckdb

from src.bronze import load_bronze_tables
from src.silver import build_silver
from src.gold import build_gold
from src.database import prepare_database
from src.settings import DATASET_DIR, DATABASE_PATH
from src.source_validation import validate_sources


def main(argv: list[str] | None = None) -> int:
    """Run all stages in order, or exactly one selected stage."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layer", choices=["all", "bronze", "silver", "gold"], default="all",
                        help="Run exactly this layer against committed inputs (default: all).")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    stages = ["bronze", "silver", "gold"] if args.layer == "all" else [args.layer]

    for stage in stages:
        logging.info("%s started", stage)
        try:
            if stage == "bronze":
                sources = validate_sources(DATASET_DIR)
                prepare_database(DATABASE_PATH)
                counts = load_bronze_tables(DATABASE_PATH, sources)
            elif stage == "silver":
                counts = {"sales_enriched": build_silver(DATABASE_PATH)}
            else:
                counts = {"monthly_sales_summary": build_gold(DATABASE_PATH)}
        except (duckdb.Error, ValueError, OSError, RuntimeError) as error:
            logging.error("%s failed: %s", stage, error)
            logging.error("Stopped. Completed upstream stages stay committed. Fix the error and retry with --layer %s.", stage)
            return 1
        for table, count in counts.items():
            logging.info("%s.%s committed: %s rows", stage, table, f"{count:,}")

    logging.info("Selected stages completed. Database: %s", DATABASE_PATH)
    if "gold" in stages:
        with duckdb.connect(str(DATABASE_PATH), read_only=True) as connection:
            print(connection.sql("""
                SELECT * FROM gold.monthly_sales_summary
                ORDER BY sales_month, product_category, sales_channel LIMIT 5
            """).df().to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
