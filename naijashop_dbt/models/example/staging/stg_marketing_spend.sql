SELECT
    campaign_id,
    campaign_name,
    channel,
    spend_date,
    clicks,
    conversions,
    amount_ngn AS marketing_spend_ngn
FROM {{ source('raw', 'marketing_spend') }}
