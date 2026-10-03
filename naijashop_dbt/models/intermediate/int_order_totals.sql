SELECT
    order_id,
    SUM(item_total_ngn) AS order_total_ngn,
    SUM(quantity) AS total_items,
    COUNT(DISTINCT product_id) AS distinct_products
FROM {{ ref('int_order_items_enriched') }}
GROUP BY order_id