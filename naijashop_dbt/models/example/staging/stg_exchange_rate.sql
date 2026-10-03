SELECT
    id,
    base_currency,
    quote_currency,
    rate,
    fetched_at,
    source
FROM {{ source('raw', 'exchange_rates') }}