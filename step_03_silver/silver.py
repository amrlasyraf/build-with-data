"""Clean and join Bronze tables with pandas, then commit Silver."""

from decimal import Decimal, InvalidOperation
from pathlib import Path
import sys

# VS Code's Run button starts this file directly, outside the project package.
if __name__ == "__main__" and not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb
import pandas as pd

from support.pipeline.stage_inputs import require_tables
from support.pipeline.settings import DATABASE_PATH


def as_integers(values: pd.Series, column: str) -> pd.Series:
    """Convert source text to whole numbers without silently truncating it."""
    try:
        numbers = pd.to_numeric(values, errors="raise")
    except (TypeError, ValueError) as error:
        raise ValueError(f"{column} contains a value that is not a number") from error
    if numbers.isna().any() or (numbers % 1 != 0).any():
        raise ValueError(f"{column} must contain whole numbers")
    return numbers.astype("int64")


def as_money(values: pd.Series, column: str) -> pd.Series:
    """Keep currency arithmetic exact while removing source formatting."""
    cleaned = values.str.strip().str.replace("$", "", regex=False).str.replace(",", "", regex=False)
    try:
        return cleaned.map(Decimal)
    except (InvalidOperation, TypeError) as error:
        raise ValueError(f"{column} contains an invalid price or cost") from error


def transform_silver(
    sales: pd.DataFrame, products: pd.DataFrame, stores: pd.DataFrame
) -> pd.DataFrame:
    """Return one cleaned, enriched row for each Bronze sales line."""
    sales = sales.copy()
    products = products.copy()
    stores = stores.copy()

    for column in ("order_number", "line_item", "customer_key", "store_key", "product_key", "quantity"):
        sales[column] = as_integers(sales[column], column)
    products["product_key"] = as_integers(products["product_key"], "product_key")
    stores["store_key"] = as_integers(stores["store_key"], "store_key")
    if (sales["quantity"] <= 0).any():
        raise ValueError("quantity must be greater than zero")

    try:
        sales["order_date"] = pd.to_datetime(sales["order_date"], format="%m/%d/%Y", errors="raise")
        sales["delivery_date"] = pd.to_datetime(
            sales["delivery_date"].str.strip().replace("", None),
            format="%m/%d/%Y",
            errors="raise",
        )
    except (TypeError, ValueError) as error:
        raise ValueError(f"A sales date could not be read: {error}") from error
    if sales["order_date"].isna().any():
        raise ValueError("order_date is required for every sales line")

    products["unit_cost_usd"] = as_money(products["unit_cost_usd"], "unit_cost_usd")
    products["unit_price_usd"] = as_money(products["unit_price_usd"], "unit_price_usd")
    products = products.rename(columns={
        "subcategory": "product_subcategory", "category": "product_category"
    })
    stores = stores.rename(columns={"country": "store_country", "state": "store_state"})

    if products["product_key"].duplicated().any() or stores["store_key"].duplicated().any():
        raise ValueError("Product/store joins failed: duplicate dimension keys")

    enriched = sales.merge(
        products[["product_key", "product_name", "brand", "product_subcategory",
                  "product_category", "unit_cost_usd", "unit_price_usd"]],
        on="product_key", how="left", validate="many_to_one", indicator="_product_match",
    )
    enriched = enriched.merge(
        stores[["store_key", "store_country", "store_state"]],
        on="store_key", how="left", validate="many_to_one", indicator="_store_match",
    )
    if (enriched["_product_match"] != "both").any() or (enriched["_store_match"] != "both").any():
        raise ValueError("Product/store joins failed: a sales key has no match")
    enriched = enriched.drop(columns=["_product_match", "_store_match"])
    category = enriched["product_category"]
    if category.isna().any() or category.astype("string").str.strip().eq("").any():
        raise ValueError("product_category is required for every sales line")

    enriched["sales_channel"] = enriched["store_key"].map(
        lambda key: "Online" if key == 0 else "In Store"
    )
    enriched["gross_sales_usd"] = enriched["quantity"] * enriched["unit_price_usd"]
    # These source prices and costs produce an estimate, not accounting profit.
    enriched["estimated_gross_profit_usd"] = enriched["quantity"] * (
        enriched["unit_price_usd"] - enriched["unit_cost_usd"]
    )
    return enriched


def build_silver(database_path: Path) -> int:
    """Read committed Bronze; replace only Silver or leave it unchanged."""
    require_tables(database_path, ["bronze.sales", "bronze.products", "bronze.stores"], "bronze")
    with duckdb.connect(str(database_path)) as connection:
        connection.execute("BEGIN TRANSACTION")
        try:
            sales = connection.execute("SELECT * FROM bronze.sales").df()
            products = connection.execute("SELECT * FROM bronze.products").df()
            stores = connection.execute("SELECT * FROM bronze.stores").df()
            enriched = transform_silver(sales, products, stores)
            if enriched.empty or len(enriched) != len(sales):
                raise ValueError("Silver row count does not match Bronze sales")

            connection.register("silver_frame", enriched)
            try:
                connection.execute("CREATE SCHEMA IF NOT EXISTS silver")
                connection.execute("""
                    CREATE OR REPLACE TABLE silver.sales_enriched AS
                    SELECT
                        CAST(order_number AS INTEGER) AS order_number,
                        CAST(line_item AS INTEGER) AS line_item,
                        CAST(order_date AS DATE) AS order_date,
                        CAST(delivery_date AS DATE) AS delivery_date,
                        CAST(customer_key AS INTEGER) AS customer_key,
                        CAST(store_key AS INTEGER) AS store_key,
                        CAST(product_key AS INTEGER) AS product_key,
                        CAST(quantity AS INTEGER) AS quantity,
                        currency_code, product_name, brand,
                        product_subcategory, product_category,
                        CAST(unit_cost_usd AS DECIMAL(12,2)) AS unit_cost_usd,
                        CAST(unit_price_usd AS DECIMAL(12,2)) AS unit_price_usd,
                        store_country, store_state, sales_channel,
                        CAST(gross_sales_usd AS DECIMAL(14,2)) AS gross_sales_usd,
                        CAST(estimated_gross_profit_usd AS DECIMAL(14,2))
                            AS estimated_gross_profit_usd,
                        current_timestamp AS loaded_at
                    FROM silver_frame
                """)
            finally:
                connection.unregister("silver_frame")

            silver_count = connection.execute("SELECT count(*) FROM silver.sales_enriched").fetchone()[0]
            if silver_count != len(sales):
                raise ValueError("Silver row count does not match Bronze sales")
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
    return silver_count


def main() -> int:
    """Build Silver when this file is run from VS Code."""
    try:
        count = build_silver(DATABASE_PATH)
    except (duckdb.Error, ValueError, OSError, RuntimeError, KeyError) as error:
        print(f"Silver failed: {error}")
        return 1
    print(f"Silver complete: {count:,} rows in silver.sales_enriched")
    print(f"Database: {DATABASE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
