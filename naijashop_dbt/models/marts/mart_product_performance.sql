WITH product_sales AS (
    SELECT
        product_id,
        SUM(quantity) AS unit_sold,
        SUM(item_total_ngn) AS sales_value_ngn,
        COUNT(DISTINCT order_id) AS number_of_orders
    FROM {{ ref('int_order_items_enriched') }}
    GROUP BY product_id
)

SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.price,
    p.stock_qty,
    COALESCE(s.unit_sold, 0) AS unit_sold,
    COALESCE(s.number_of_orders, 0) AS number_of_orders,
    COALESCE(s.sales_value_ngn, 0) AS sales_value_ngn
FROM {{ ref('stg_products') }} AS p
LEFT JOIN product_sales AS s
    ON p.product_id = s.product_id