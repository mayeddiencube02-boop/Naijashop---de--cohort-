"""
NaijaShop seed data generator.

Generates realistic synthetic e-commerce data (customers, products, orders,
order_items, payments) as CSVs, ready to load into Postgres for the cohort
project. Includes a small amount of deliberate real-world messiness
(nulls, missing emails) so learners get practice handling imperfect data --
this is intentional, not a bug.

Usage:
    python seed_data.py                # writes CSVs to ./data/
    python seed_data.py --load-pg      # also loads them into Postgres
"""

import argparse
import csv
import os
import random
from datetime import datetime, timedelta

from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

OUTPUT_DIR = "data"

NIGERIAN_FIRST_NAMES = [
    "Amina", "Ibrahim", "Chidinma", "Emeka", "Fatima", "Oluwaseun", "Yusuf",
    "Ngozi", "Abdullahi", "Blessing", "Chukwuemeka", "Zainab", "Tunde",
    "Halima", "Obinna", "Kemi", "Musa", "Chiamaka", "Suleiman", "Adaeze",
    "Bashir", "Funke", "Nnamdi", "Aisha", "Segun", "Rukayya", "Uche",
    "Hauwa", "Damilola", "Aliyu",
]

NIGERIAN_LAST_NAMES = [
    "Abubakar", "Okafor", "Bello", "Adeyemi", "Mohammed", "Eze", "Yakubu",
    "Okonkwo", "Suleiman", "Nwachukwu", "Garba", "Adamu", "Chukwu",
    "Sani", "Okoro", "Danjuma", "Nwosu", "Ahmed", "Ibrahim", "Balogun",
]


def nigerian_name():
    return f"{random.choice(NIGERIAN_FIRST_NAMES)} {random.choice(NIGERIAN_LAST_NAMES)}"


NIGERIAN_CITIES = [
    ("Kano", "Kano"), ("Lagos", "Lagos"), ("Abuja", "FCT"),
    ("Ibadan", "Oyo"), ("Kaduna", "Kaduna"), ("Port Harcourt", "Rivers"),
    ("Benin City", "Edo"), ("Enugu", "Enugu"), ("Jos", "Plateau"),
    ("Abeokuta", "Ogun"),
]

PRODUCT_CATALOG = {
    "Electronics": ["Wireless Earbuds", "Power Bank 20000mAh", "Bluetooth Speaker",
                     "Phone Case", "USB-C Cable", "Smart Watch"],
    "Fashion": ["Ankara Fabric", "Men's Sneakers", "Women's Handbag",
                "Kaftan", "Sunglasses", "Wristwatch"],
    "Home & Kitchen": ["Blender", "Non-stick Pan Set", "Electric Kettle",
                        "Storage Containers", "Standing Fan"],
    "Beauty": ["Shea Butter Cream", "Turmeric Soap", "Hair Oil",
               "Facial Cleanser", "Perfume Oil"],
    "Groceries": ["Rice 5kg Bag", "Palm Oil 1L", "Spaghetti Pack", "Tea Sachets"],
}

PAYMENT_METHODS = ["card", "bank_transfer", "ussd", "cash_on_delivery"]
ORDER_STATUSES = ["pending", "paid", "shipped", "delivered", "cancelled"]


def gen_customers(n):
    rows = []
    for i in range(1, n + 1):
        city, state = random.choice(NIGERIAN_CITIES)
        name = nigerian_name()
        # ~4% missing email on purpose - realistic data quality issue for Week 3 teaching
        if random.random() > 0.04:
            email = f"{name.lower().replace(' ', '.')}{i}@example.com"
        else:
            email = ""
        rows.append({
            "customer_id": i,
            "full_name": name,
            "email": email,
            "city": city,
            "state": state,
            "signup_date": fake.date_between(start_date="-2y", end_date="-1d"),
        })
    return rows


def gen_products(n_per_category=8):
    rows = []
    pid = 1
    for category, names in PRODUCT_CATALOG.items():
        for _ in range(n_per_category):
            name = random.choice(names)
            price = round(random.uniform(1500, 85000), 2)  # NGN price range
            rows.append({
                "product_id": pid,
                "product_name": f"{name} - {fake.word().capitalize()}",
                "category": category,
                "price": price,
                "stock_qty": random.randint(0, 500),
            })
            pid += 1
    return rows


def gen_orders(n_orders, n_customers):
    rows = []
    for i in range(1, n_orders + 1):
        order_date = fake.date_time_between(start_date="-1y", end_date="now")
        rows.append({
            "order_id": i,
            "customer_id": random.randint(1, n_customers),
            "order_date": order_date,
            "status": random.choices(
                ORDER_STATUSES, weights=[5, 15, 15, 55, 10]
            )[0],
        })
    return rows


def gen_order_items(orders, products):
    rows = []
    item_id = 1
    for order in orders:
        n_items = random.randint(1, 5)
        chosen = random.sample(products, k=min(n_items, len(products)))
        for product in chosen:
            rows.append({
                "order_item_id": item_id,
                "order_id": order["order_id"],
                "product_id": product["product_id"],
                "quantity": random.randint(1, 4),
                "unit_price": product["price"],  # price captured at order time
            })
            item_id += 1
    return rows


def gen_payments(orders, order_items):
    rows = []
    totals = {}
    for item in order_items:
        totals[item["order_id"]] = totals.get(item["order_id"], 0) + (
            item["quantity"] * float(item["unit_price"])
        )

    for i, order in enumerate(orders, start=1):
        amount = round(totals.get(order["order_id"], 0), 2)
        paid = order["status"] in ("paid", "shipped", "delivered")
        rows.append({
            "payment_id": i,
            "order_id": order["order_id"],
            "method": random.choice(PAYMENT_METHODS),
            "amount": amount,
            "status": "successful" if paid else random.choice(["pending", "failed"]),
            "paid_at": order["order_date"] + timedelta(minutes=random.randint(2, 120))
                       if paid else "",
        })
    return rows


def write_csv(rows, filename):
    if not rows:
        return
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {len(rows):>6} rows -> {path}")


def load_to_postgres(dsn):
    import psycopg2

    conn = psycopg2.connect(dsn)
    cur = conn.cursor()

    with open("schema.sql") as f:
        cur.execute(f.read())
    conn.commit()

    for table, cols in [
        ("customers", ["customer_id", "full_name", "email", "city", "state", "signup_date"]),
        ("products", ["product_id", "product_name", "category", "price", "stock_qty"]),
        ("orders", ["order_id", "customer_id", "order_date", "status"]),
        ("order_items", ["order_item_id", "order_id", "product_id", "quantity", "unit_price"]),
        ("payments", ["payment_id", "order_id", "method", "amount", "status", "paid_at"]),
    ]:
        path = os.path.join(OUTPUT_DIR, f"{table}.csv")
        with open(path) as f:
            next(f)  # skip header
            cur.copy_expert(
                f"COPY {table} ({', '.join(cols)}) FROM STDIN WITH CSV NULL ''", f
            )
        conn.commit()
        print(f"  loaded {table} into Postgres")

    cur.close()
    conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--customers", type=int, default=500)
    parser.add_argument("--orders", type=int, default=2000)
    parser.add_argument("--load-pg", action="store_true",
                         help="also load the CSVs into Postgres")
    parser.add_argument("--dsn", default="dbname=naijashop user=postgres password=postgres host=localhost",
                         help="Postgres connection string, used only with --load-pg")
    args = parser.parse_args()

    print("Generating NaijaShop seed data...")
    customers = gen_customers(args.customers)
    products = gen_products()
    orders = gen_orders(args.orders, args.customers)
    order_items = gen_order_items(orders, products)
    payments = gen_payments(orders, order_items)

    write_csv(customers, "customers.csv")
    write_csv(products, "products.csv")
    write_csv(orders, "orders.csv")
    write_csv(order_items, "order_items.csv")
    write_csv(payments, "payments.csv")

    if args.load_pg:
        print("Loading into Postgres...")
        load_to_postgres(args.dsn)

    print("Done.")


if __name__ == "__main__":
    main()
