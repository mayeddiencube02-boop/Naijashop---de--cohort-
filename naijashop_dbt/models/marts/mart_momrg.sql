WITH monthly_revenue AS (

    SELECT
        DATE_TRUNC('month', order_date::DATE) AS month,
        COUNT(*) AS total_orders,
        SUM(order_total_ngn) AS revenue_ngn
    FROM {{ ref('fct_orders') }}
    GROUP BY 1
),

with_previous_month AS (
    SELECT
        month,
        total_orders,
        revenue_ngn,
        LAG(revenue_ngn) OVER (ORDER BY month) AS previous_month_revenue_ngn
    FROM monthly_revenue
)

SELECT
    month,
    total_orders,
    revenue_ngn,
    previous_month_revenue_ngn,
    ROUND(
        (revenue_ngn - previous_month_revenue_ngn) / NULLIF(previous_month_revenue_ngn, 0) * 100,
        2
    ) AS revenue_growth_pct

FROM with_previous_month
