-- Parse source text once before joining. Source dates use month/day/year.
CREATE OR REPLACE TABLE silver.sales_enriched AS
WITH sales AS (
    SELECT
        CAST(order_number AS INTEGER) AS order_number,
        CAST(line_item AS INTEGER) AS line_item,
        CAST(strptime(order_date, '%m/%d/%Y') AS DATE) AS order_date,
        CAST(strptime(NULLIF(trim(delivery_date), ''), '%m/%d/%Y') AS DATE) AS delivery_date,
        CAST(customer_key AS INTEGER) AS customer_key,
        CAST(store_key AS INTEGER) AS store_key,
        CAST(product_key AS INTEGER) AS product_key,
        CAST(quantity AS INTEGER) AS quantity,
        currency_code
    FROM bronze.sales
), products AS (
    SELECT
        CAST(product_key AS INTEGER) AS product_key,
        product_name, brand,
        subcategory AS product_subcategory,
        category AS product_category,
        CAST(replace(replace(trim(unit_cost_usd), '$', ''), ',', '') AS DECIMAL(12,2)) AS unit_cost_usd,
        CAST(replace(replace(trim(unit_price_usd), '$', ''), ',', '') AS DECIMAL(12,2)) AS unit_price_usd
    FROM bronze.products
), stores AS (
    SELECT CAST(store_key AS INTEGER) AS store_key,
           country AS store_country, state AS store_state
    FROM bronze.stores
)
SELECT
    s.*,
    p.product_name, p.brand, p.product_subcategory, p.product_category,
    p.unit_cost_usd, p.unit_price_usd,
    st.store_country, st.store_state,
    CASE WHEN s.store_key = 0 THEN 'Online' ELSE 'In Store' END AS sales_channel,
    CAST(s.quantity * p.unit_price_usd AS DECIMAL(14,2)) AS gross_sales_usd,
    -- Standard product prices and costs give an estimate, not accounting profit.
    CAST(s.quantity * (p.unit_price_usd - p.unit_cost_usd) AS DECIMAL(14,2)) AS estimated_gross_profit_usd,
    current_timestamp AS loaded_at
FROM sales AS s
LEFT JOIN products AS p ON s.product_key = p.product_key
LEFT JOIN stores AS st ON s.store_key = st.store_key;
