WITH customer_metrics AS (
    SELECT
        customer_id,
        COUNT(*) AS total_orders,
        SUM(order_total_ngn) AS lifetime_value_ngn,
        AVG(order_total_ngn) AS average_order_value_ngn,
        MIN(order_date) AS first_order_date,
        MAX(order_date) AS last_order_date
    FROM {{ ref('fct_orders') }}
    GROUP BY customer_id
)

SELECT
    c.customer_id,
    c.full_name,
    c.email,
    c.city,
    c.state,
    c.signup_date,

    COALESCE(
        m.total_orders,
        0
    ) AS total_orders,

    COALESCE(
        m.lifetime_value_ngn,
        0
    ) AS lifetime_value_ngn,

    COALESCE(
        m.average_order_value_ngn,
        0
    ) AS average_order_value_ngn,

    m.first_order_date,
    m.last_order_date

FROM {{ ref('dim_customers') }} c
LEFT JOIN customer_metrics m
    ON c.customer_id = m.customer_id
    