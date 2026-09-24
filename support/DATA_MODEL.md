# Data Model and Table Contracts

This document describes the tables created by the local pipeline. Column names
use `snake_case` in DuckDB even though the CSV headers contain spaces. The
tables use the `bronze`, `silver`, and `gold` schemas in one DuckDB file.

## Grain and Keys

| Table | One row represents | Key |
|---|---|---|
| `bronze.sales` | One product line within an order | `(order_number, line_item)` |
| `bronze.products` | One product | `product_key` |
| `bronze.stores` | One physical or online store | `store_key` |
| `silver.sales_enriched` | One cleaned and enriched sales line | `(order_number, line_item)` |
| `gold.monthly_sales_summary` | One month, category, and channel combination | `(sales_month, product_category, sales_channel)` |

## Bronze Contracts

Bronze keeps the source fields recognizable. Source values, including dates and
numbers, are loaded as text so pandas can handle their types in Silver.

### `bronze.sales`

| Column | Source header | Meaning |
|---|---|---|
| `order_number` | `Order Number` | Order identifier |
| `line_item` | `Line Item` | Product-line identifier within the order |
| `order_date` | `Order Date` | Date the order was placed |
| `delivery_date` | `Delivery Date` | Delivery date; blank is valid for in-store sales |
| `customer_key` | `CustomerKey` | Customer identifier retained for future extensions |
| `store_key` | `StoreKey` | Store identifier; `0` means online |
| `product_key` | `ProductKey` | Purchased product identifier |
| `quantity` | `Quantity` | Number of units purchased |
| `currency_code` | `Currency Code` | Currency used to process the order |
| `loaded_at` | generated | Timestamp for the pipeline load |
| `source_file` | generated | Name of the source CSV |

### `bronze.products`

| Column | Source header | Meaning |
|---|---|---|
| `product_key` | `ProductKey` | Product identifier |
| `product_name` | `Product Name` | Product description |
| `brand` | `Brand` | Product brand |
| `color` | `Color` | Product color |
| `unit_cost_usd` | `Unit Cost USD` | Unit cost stored as source text in Bronze |
| `unit_price_usd` | `Unit Price USD` | Unit price stored as source text in Bronze |
| `subcategory_key` | `SubcategoryKey` | Product subcategory identifier |
| `subcategory` | `Subcategory` | Product subcategory name |
| `category_key` | `CategoryKey` | Product category identifier |
| `category` | `Category` | Product category name |
| `loaded_at` | generated | Timestamp for the pipeline load |
| `source_file` | generated | Name of the source CSV |

### `bronze.stores`

| Column | Source header | Meaning |
|---|---|---|
| `store_key` | `StoreKey` | Store identifier |
| `country` | `Country` | Store country |
| `state` | `State` | Store state or region |
| `square_meters` | `Square Meters` | Store area; blank is valid for the online store |
| `open_date` | `Open Date` | Date the store opened |
| `loaded_at` | generated | Timestamp for the pipeline load |
| `source_file` | generated | Name of the source CSV |

## Silver Contract

### `silver.sales_enriched`

All columns below are typed and analytics-ready.

| Column | Type | Rule |
|---|---|---|
| `order_number` | `integer` | From sales |
| `line_item` | `integer` | From sales |
| `order_date` | `date` | Parse the source order date |
| `delivery_date` | `date` | Parse when present; otherwise `NULL` |
| `customer_key` | `integer` | From sales; no customer join in Project #1 |
| `store_key` | `integer` | From sales |
| `product_key` | `integer` | From sales |
| `quantity` | `integer` | Must be greater than zero |
| `currency_code` | `varchar` | Retained as source context |
| `product_name` | `text` | From products |
| `brand` | `text` | From products |
| `product_subcategory` | `text` | From products |
| `product_category` | `text` | From products |
| `unit_cost_usd` | `numeric(12,2)` | Pandas removes `$`, commas, and whitespace and calculates with decimal values |
| `unit_price_usd` | `numeric(12,2)` | Pandas removes `$`, commas, and whitespace and calculates with decimal values |
| `store_country` | `text` | From stores |
| `store_state` | `text` | From stores |
| `sales_channel` | `text` | `Online` for store `0`, otherwise `In Store` |
| `gross_sales_usd` | `numeric(14,2)` | `quantity * unit_price_usd` |
| `estimated_gross_profit_usd` | `numeric(14,2)` | `quantity * (unit_price_usd - unit_cost_usd)` |
| `loaded_at` | `timestamp with time zone` | Timestamp for the transformation run |

## Gold Contract

### `gold.monthly_sales_summary`

| Column | Type | Rule |
|---|---|---|
| `sales_month` | `date` | First day of the order month |
| `product_category` | `text` | Grouping from Silver |
| `sales_channel` | `text` | `Online` or `In Store` |
| `line_item_count` | `bigint` | Count of sales lines |
| `units_sold` | `bigint` | Sum of quantity |
| `gross_sales_usd` | `numeric(16,2)` | Sum of Silver gross sales |
| `estimated_gross_profit_usd` | `numeric(16,2)` | Sum of Silver estimated gross profit |

## Join Rules

```text
bronze.sales.product_key = bronze.products.product_key
bronze.sales.store_key   = bronze.stores.store_key
```

Both are many-to-one joins. The Silver row count must therefore match the Bronze
sales row count. The pipeline rejects a missing or duplicate product or store
key instead of silently dropping or multiplying transactions.

## Intentional Omissions

- Customers are not joined in Project #1 because they are unnecessary for the
  chosen business question.
- Exchange rates are not used because the product file already supplies USD
  price and cost fields.
- No currency-normalized transaction amount is claimed; the project calculates
  teaching metrics from the supplied USD product values.
- No discount, tax, refund, or actual accounting-profit fields are available.
