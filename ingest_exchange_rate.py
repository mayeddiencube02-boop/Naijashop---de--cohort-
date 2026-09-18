"""
NaijaShop currency ingestion script (Week 4-5)

WHAT THIS SCRIPT DOES, IN ONE SENTENCE:
Fetches "1 USD = how many NGN" from a free API, and saves that number
plus a timestamp as a new row in a Postgres table called exchange_rates.

Run it once a day (manually today, via Airflow later in the course) and
you build up a real history of exchange rates over time - a second,
independent data source alongside your NaijaShop order data.
"""

# argparse lets us accept command-line options like --dsn, so the same
# script can point at different databases without editing the code
import argparse

# sys lets us exit the script with a specific error code (1 = failure)
# when something goes wrong, instead of letting Python crash messily
import sys

# datetime/timezone give us a fallback timestamp if the API doesn't
# include one in its response
from datetime import datetime, timezone

# requests is the standard Python library for calling web APIs -
# this is the tool that actually reaches out to the internet
import requests

# The base URL of the free currency API we're pulling from.
# No API key needed - confirmed to support NGN.
API_URL = "https://www.currencyexchangetool.com/api/v1/convert"

# This SQL creates our destination table, but only if it doesn't
# already exist - "IF NOT EXISTS" means running this twice is safe,
# it won't wipe out data you already collected
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS exchange_rates (
    id              SERIAL PRIMARY KEY,
    base_currency   VARCHAR(3) NOT NULL,   -- e.g. 'USD'
    quote_currency  VARCHAR(3) NOT NULL,   -- e.g. 'NGN'
    rate            NUMERIC(14, 6) NOT NULL,  -- e.g. 1530.450000
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT now(),  -- when the RATE was valid
    source          VARCHAR(60) NOT NULL DEFAULT 'currencyexchangetool.com'
);
"""

# This is the SQL template for adding ONE new row of data.
# The %s placeholders get safely filled in later - this is called a
# "parameterized query" and it protects against SQL injection attacks,
# which matters even in a teaching project since it's a real-world habit
INSERT_SQL = """
INSERT INTO exchange_rates (base_currency, quote_currency, rate, fetched_at, source)
VALUES (%s, %s, %s, %s, %s);
"""


def fetch_rate(base: str, quote: str) -> dict:
    """Call the exchange rate API. Raises on any non-2xx or malformed response."""

    # This is the actual network call - it sends a GET request to the API
    # with our currency pair as query parameters (e.g. ?amount=1&from=USD&to=NGN)
    # timeout=10 means: if the API doesn't respond within 10 seconds, give up
    # instead of hanging forever
    resp = requests.get(
        API_URL,
        params={"amount": 1, "from": base, "to": quote},
        timeout=10,
    )

    # If the API returned an error status code (like 404 or 500),
    # this line raises an exception immediately instead of silently
    # continuing with broken data
    resp.raise_for_status()

    # Convert the API's raw text response into a Python dictionary
    # so we can pull specific fields out of it, like data["rate"]
    data = resp.json()

    # Even if the HTTP request "succeeded", the API might still report
    # a business-logic failure inside the response body (e.g. unsupported
    # currency code) - this check catches that case too
    if not data.get("success"):
        raise ValueError(f"API returned an error payload: {data}")

    return data


def load_to_postgres(dsn: str, base: str, quote: str, rate: float, fetched_at: str):
    """Insert one exchange rate row into Postgres."""

    # psycopg2 is only imported here (not at the top of the file) so that
    # the fetch_rate() function above can be tested on its own without
    # needing a database connection available
    import psycopg2

    # Open a connection to Postgres using the connection string (dsn)
    # passed in from the command line, e.g.
    # "dbname=naijashop user=postgres password=Joe4529 host=localhost"
    conn = psycopg2.connect(dsn)

    # A "cursor" is how you actually send SQL commands over that connection
    cur = conn.cursor()

    # Make sure the table exists before we try to insert into it
    cur.execute(CREATE_TABLE_SQL)

    # Run the INSERT, safely substituting our actual values into the
    # %s placeholders from INSERT_SQL above
    cur.execute(INSERT_SQL, (base, quote, rate, fetched_at, "currencyexchangetool.com"))

    # Nothing is actually saved to the database until you call commit() -
    # this is Postgres's safety mechanism so partial/broken writes don't
    # get saved accidentally
    conn.commit()

    # Always close what you open - frees up the connection for other uses
    cur.close()
    conn.close()


def main():
    # Set up the command-line options this script accepts
    parser = argparse.ArgumentParser()

    # --base and --quote let you pull a different currency pair later
    # (e.g. --base GBP --quote NGN) without touching the code
    parser.add_argument("--base", default="USD")
    parser.add_argument("--quote", default="NGN")

    # --dsn is the database connection string - has a sensible default
    # but you can override it to point at a different database/password
    parser.add_argument(
        "--dsn",
        default="dbname=naijashop user=postgres password=postgress host=localhost",
    )

    # Actually read whatever the user typed after the script name
    args = parser.parse_args()

    print(f"Fetching {args.base}->{args.quote} rate...")

    # try/except here means: if fetch_rate() fails for any reason
    # (no internet, API is down, bad currency code), we print a clear
    # error message and stop - instead of crashing with a confusing
    # Python traceback that a beginner can't easily read
    try:
        data = fetch_rate(args.base, args.quote)
    except Exception as e:
        print(f"ERROR: could not fetch exchange rate: {e}", file=sys.stderr)
        sys.exit(1)  # exit code 1 signals "something went wrong" to the OS

    # Pull the actual numbers out of the API's response dictionary
    rate = data["rate"]

    # Use the timestamp the API gave us; if for some reason it's missing,
    # fall back to "right now" in UTC
    fetched_at = data.get("updatedAt", datetime.now(timezone.utc).isoformat())

    print(f"  1 {args.base} = {rate} {args.quote}  (as of {fetched_at})")

    # Same defensive pattern as above - if the database write fails
    # (wrong password, Postgres not running), fail clearly and stop
    try:
        load_to_postgres(args.dsn, args.base, args.quote, rate, fetched_at)
    except Exception as e:
        print(f"ERROR: could not load into Postgres: {e}", file=sys.stderr)
        sys.exit(1)

    print("Loaded into exchange_rates table.")


# This is a Python convention: only run main() if this file is executed
# directly (python ingest_exchange_rate.py), not if it's imported by
# another script - this is what let me test fetch_rate() and
# load_to_postgres() separately earlier, without running the whole script
if __name__ == "__main__":
    main()
