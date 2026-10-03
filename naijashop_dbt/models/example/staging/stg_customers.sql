SELECT
    customer_id,
    full_name,
    email,
    city,
    state,
    signup_date
FROM {{ source('raw', 'customers') }}
