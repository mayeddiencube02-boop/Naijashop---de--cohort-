SELECT
    campaign_id,
    campaign_name,
    channel,
    SUM(clicks) AS total_clicks,
    SUM(conversions) AS total_conversions,
    SUM(marketing_spend_ngn) AS total_spend_ngn,

    ROUND(
        SUM(marketing_spend_ngn) / NULLIF(SUM(clicks), 0),
        2
    ) AS cost_per_click,

    ROUND(
        SUM(marketing_spend_ngn) / NULLIF(SUM(conversions), 0),
        2
    ) AS cost_per_conversion,

    ROUND(
        (SUM(conversions)::numeric / NULLIF(SUM(clicks), 0)) * 100,
        2
    ) AS conversion_rate_pct

FROM {{ ref('stg_marketing_spend') }}
GROUP BY campaign_id,
         campaign_name,
         channel