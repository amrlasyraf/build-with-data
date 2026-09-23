-- One row per order month, product category, and sales channel.
CREATE OR REPLACE TABLE gold.monthly_sales_summary AS
SELECT
    CAST(date_trunc('month', order_date) AS DATE) AS sales_month,
    product_category,
    sales_channel,
    count(*) AS line_item_count,
    CAST(sum(quantity) AS BIGINT) AS units_sold,
    CAST(sum(gross_sales_usd) AS DECIMAL(16,2)) AS gross_sales_usd,
    CAST(sum(estimated_gross_profit_usd) AS DECIMAL(16,2)) AS estimated_gross_profit_usd
FROM silver.sales_enriched
GROUP BY sales_month, product_category, sales_channel;
