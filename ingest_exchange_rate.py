"""
NaijaShop currency ingestion script (Week 4-5)

WHAT THIS SCRIPT DOES, IN ONE SENTENCE:
Fetches "1 USD = how many NGN" from a free API, and saves that number
plus a timestamp as a new row in a Postgres table called exchange_rates.

Run it once a day (manually today, via Airflow later in the course) and
you build up a real history of exchange rates over time - a second,
independent data source alongside your NaijaShop order data.
"""

import argparse
import sys
from datetime import datetime, timezone
import requests

API_URL = "https://open.er-api.com/v6/latest"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS exchange_rates (
    id              SERIAL PRIMARY KEY,
    base_currency   VARCHAR(3) NOT NULL,
    quote_currency  VARCHAR(3) NOT NULL,
    rate            NUMERIC(14, 6) NOT NULL,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    source          VARCHAR(60) NOT NULL DEFAULT 'exchangerate-api.com'
);
"""

INSERT_SQL = """
INSERT INTO exchange_rates (base_currency, quote_currency, rate, fetched_at, source)
VALUES (%s, %s, %s, %s, %s);
"""


def fetch_rate(base: str, quote: str) -> dict:
    resp = requests.get(f"{API_URL}/{base}", timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("result") != "success":
        raise ValueError(f"API returned an error payload: {data}")
    if quote not in data.get("rates", {}):
        raise ValueError(f"'{quote}' not found in API response rates")
    return {
        "rate": data["rates"][quote],
        "updatedAt": data.get("time_last_update_utc"),
    }


def load_to_postgres(dsn: str, base: str, quote: str, rate: float, fetched_at: str):
    import psycopg2
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)
    cur.execute(INSERT_SQL, (base, quote, rate, fetched_at, "exchangerate-api.com"))
    conn.commit()
    cur.close()
    conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="USD")
    parser.add_argument("--quote", default="NGN")
    parser.add_argument(
        "--dsn",
        default="dbname=naijashop user=postgres password=postgres host=localhost",
    )
    args = parser.parse_args()

    print(f"Fetching {args.base}->{args.quote} rate...")

    try:
        data = fetch_rate(args.base, args.quote)
    except Exception as e:
        print(f"ERROR: could not fetch exchange rate: {e}", file=sys.stderr)
        sys.exit(1)

    rate = data["rate"]
    fetched_at = data.get("updatedAt") or datetime.now(timezone.utc).isoformat()

    print(f"  1 {args.base} = {rate} {args.quote}  (as of {fetched_at})")

    try:
        load_to_postgres(args.dsn, args.base, args.quote, rate, fetched_at)
    except Exception as e:
        print(f"ERROR: could not load into Postgres: {e}", file=sys.stderr)
        sys.exit(1)

    print("Loaded into exchange_rates table.")


if __name__ == "__main__":
    main()
