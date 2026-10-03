SELECT
    product_id,
    product_name,
    category,
    price,
    stock_qty
FROM {{ source('raw', 'products') }}
