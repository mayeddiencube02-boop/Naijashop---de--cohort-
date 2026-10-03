# NaijaShop Data Pipeline

A consolidated e-commerce analytics pipeline for NaijaShop, built on **Neon (serverless Postgres)** and transformed with **dbt**. The data is now modeled and ready to connect directly to **Power BI** for analysis and dashboarding.

---

## Overview

This project ingests data from multiple sources, consolidates it into a single Postgres database (Neon), and transforms it through a layered dbt pipeline into analysis-ready marts. The end result is a set of clean, documented tables that can be plugged straight into Power BI without further cleanup.

## Data Sources

| Source | Method | Destination Table |
|---|---|---|
| Synthetic customer/order data (Faker) | `seed_data.py` | `customers`, `products`, `orders`, `order_items`, `payments` |
| Marketing spend (Google Sheet) | Google Sheets API (`ingest_marketing_sheets_api_class.py`) | `marketing_spend` |
| Daily USD→NGN exchange rate | Free API via `ingest_exchange_rate.py` (open.er-api.com) | `exchange_rates` |

All raw data lands in the `public` schema on Neon, which acts as the single source of truth for the whole pipeline.

## Database

- **Host:** Neon serverless Postgres (`neondb`)
- **Schema:** `public`
- Connection requires `sslmode=require`

## Orchestration

A GitHub Actions workflow (`.github/workflows/pipeline.yml`) runs daily and can also be triggered manually:
- Refreshes seed data directly against Neon
- Triggers downstream syncs via Airbyte Cloud (exchange rate and marketing spend connections)

> **Note:** Airbyte sync-trigger permissions are still being finalized on the GitHub Actions side; Airbyte's own internal schedule (hourly/daily, configured in the Airbyte dashboard) keeps data flowing independently of this.

## Transformation Layer (dbt)

Project: `naijashop_dbt`, connected to Neon via `profiles.yml` (target: `dev`).

The pipeline follows a standard layered dbt architecture:

```
Raw tables  →  Staging views  →  Intermediate views  →  Marts
```

### Staging (`models/example/staging/`)
One clean view per raw source table, 1:1 column mapping:
- `stg_customers`
- `stg_orders`
- `stg_order_items`
- `stg_products`
- `stg_payments`
- `stg_marketing_spend`
- `stg_exchange_rate`

### Intermediate (`models/intermediate/`)
Reusable joined/aggregated building blocks:
- `int_order_items_enriched` — order items joined with product details, computes `item_total_ngn`
- `int_order_totals` — per-order aggregates (total value, item count, distinct products)

### Marts (`models/marts/`)
Business-ready tables, each built for a specific analysis use case:

| Mart | Grain | What it's for |
|---|---|---|
| `fct_orders` | One row per order | Core order fact table with totals |
| `mart_customer_360` | One row per customer | Lifetime value, order frequency, activity dates |
| `mart_product_performance` | One row per product | Units sold, revenue, order count per product |
| `mart_daily_revenue` | One row per day | Daily revenue and order trend |
| `mart_marketing_perfomance` | One row per campaign | Spend, clicks, conversions, cost-per-click/conversion |
| `mart_momrg` | One row per month | Month-over-month revenue growth |
| `mart_rfm_customer_segmentation` | One row per customer | Recency/Frequency/Monetary customer segments |

All marts are tested (`not_null`, `unique` on key columns) and build cleanly via:
```bash
dbt build
```

---

## Connecting Power BI

The database is ready for direct connection — no additional transformation needed on the Power BI side.

1. In Power BI Desktop: **Get Data → More → Database → PostgreSQL database**
2. Enter the Neon connection details:
   - **Server:** `<your-neon-host>:5432`
   - **Database:** `neondb`
3. Choose **Import** or **DirectQuery** depending on refresh needs
4. Under advanced options, ensure SSL is enabled (Power BI's Postgres connector handles `sslmode=require` automatically for Neon)
5. Authenticate with your Neon database credentials
6. In Navigator, select the schema `public` and choose the **mart tables** (`fct_orders`, `mart_customer_360`, `mart_product_performance`, `mart_daily_revenue`, `mart_marketing_perfomance`, `mart_momrg`, `mart_rfm_customer_segmentation`) rather than raw or staging tables — these are the ones built specifically for reporting

### Recommended starting dashboards
- **Revenue overview** — `mart_daily_revenue` + `mart_momrg` for trend and growth tracking
- **Customer insights** — `mart_customer_360` + `mart_rfm_customer_segmentation` for segmentation and LTV
- **Product performance** — `mart_product_performance` for top sellers and category breakdowns
- **Marketing ROI** — `mart_marketing_perfomance` for cost-per-click/conversion by channel

---

## Refreshing the Data

- Re-run ingestion scripts manually, or let the scheduled GitHub Action handle it daily
- After new raw data lands, rebuild the dbt layer:
```bash
cd naijashop_dbt
dbt build
```
- In Power BI, use **Refresh** (Import mode) or rely on **DirectQuery** for live data

---

## Project Status

✅ Raw data ingestion (seed data, marketing spend, exchange rates)
✅ Consolidated on Neon as single source of truth
✅ Full dbt transformation layer (staging → intermediate → marts)
✅ Data tests passing on key models
✅ Ready for Power BI connection
🔄 GitHub Actions / Airbyte sync automation — in progress
