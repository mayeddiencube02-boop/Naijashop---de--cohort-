SELECT
    o.order_id,
    o.customer_id,
    o.order_date,
    o.status,

    COALESCE(
        t.order_total_ngn,
        0
    ) AS order_total_ngn,

    COALESCE(
        t.total_items,
        0
    ) AS total_items,

    COALESCE(
        t.distinct_products,
        0
    ) AS distinct_products

FROM {{ ref('stg_orders') }} o
LEFT JOIN {{ ref('int_order_totals') }} t
    ON o.order_id = t.order_id