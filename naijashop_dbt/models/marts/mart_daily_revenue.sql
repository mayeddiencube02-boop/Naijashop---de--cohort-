SELECT
      order_date,
      COUNT(*) AS total_orders,
      COUNT(DISTINCT customer_id) AS unique_customers,
      SUM(order_total_ngn) AS order_value_ngn,
      AVG(order_total_ngn) AS average_order_value_ngn,
      SUM(total_items) AS total_items
      FROM {{ref('fct_orders')}}
      GROUP BY order_date