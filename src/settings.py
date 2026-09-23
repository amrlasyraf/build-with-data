"""Paths and source contracts used by the core pipeline."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = PROJECT_ROOT / "step_01_data"
LOCAL_DIR = PROJECT_ROOT / "_local"
OUTPUT_DIR = LOCAL_DIR / "output"
DATABASE_PATH = OUTPUT_DIR / "retail_pipeline.duckdb"

SOURCE_COLUMNS = {
    "Sales.csv": [
        "Order Number",
        "Line Item",
        "Order Date",
        "Delivery Date",
        "CustomerKey",
        "StoreKey",
        "ProductKey",
        "Quantity",
        "Currency Code",
    ],
    "Products.csv": [
        "ProductKey",
        "Product Name",
        "Brand",
        "Color",
        "Unit Cost USD",
        "Unit Price USD",
        "SubcategoryKey",
        "Subcategory",
        "CategoryKey",
        "Category",
    ],
    "Stores.csv": [
        "StoreKey",
        "Country",
        "State",
        "Square Meters",
        "Open Date",
    ],
}

BRONZE_TABLE_NAMES = {
    "Sales.csv": "sales",
    "Products.csv": "products",
    "Stores.csv": "stores",
}

BRONZE_COLUMN_NAMES = {
    "Sales.csv": [
        "order_number",
        "line_item",
        "order_date",
        "delivery_date",
        "customer_key",
        "store_key",
        "product_key",
        "quantity",
        "currency_code",
    ],
    "Products.csv": [
        "product_key",
        "product_name",
        "brand",
        "color",
        "unit_cost_usd",
        "unit_price_usd",
        "subcategory_key",
        "subcategory",
        "category_key",
        "category",
    ],
    "Stores.csv": [
        "store_key",
        "country",
        "state",
        "square_meters",
        "open_date",
    ],
}

MEDALLION_SCHEMAS = ("bronze", "silver", "gold")
