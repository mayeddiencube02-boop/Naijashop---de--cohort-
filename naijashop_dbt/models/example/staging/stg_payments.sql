SELECT
    payment_id,
    order_id,
    method,
    amount,
    status,
    paid_at
FROM {{ source('raw', 'payments') }}
