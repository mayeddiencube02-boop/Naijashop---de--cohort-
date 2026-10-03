WITH customer_metrics AS (
    SELECT
        customer_id,
        COUNT(*) AS frequency,
        SUM(order_total_ngn) AS monetary_value_ngn,
        MAX(order_date) AS last_order_date
    FROM {{ ref('fct_orders') }}
    GROUP BY customer_id
)
SELECT
    customer_id,
    last_order_date,
    CURRENT_DATE - last_order_date::DATE AS recency_days,
    frequency,
    monetary_value_ngn,
    CASE
        WHEN (CURRENT_DATE - last_order_date::DATE <= 30) AND frequency >= 5 THEN 'Frequency Recent Customer'
        WHEN (CURRENT_DATE - last_order_date::DATE <= 90) AND frequency >= 2 THEN 'Repeat Customer'
        WHEN (CURRENT_DATE - last_order_date::DATE <= 90) THEN 'Needs Attention'
        ELSE 'other'
    END AS customer_segment
FROM customer_metrics
