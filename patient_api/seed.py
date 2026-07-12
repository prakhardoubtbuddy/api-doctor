"""Seed patient.db with enough rows that the flaws are actually slow.
Run once: python3 seed.py"""
import sqlite3, os, random

DB = os.path.join(os.path.dirname(__file__), "patient.db")
if os.path.exists(DB):
    os.remove(DB)

conn = sqlite3.connect(DB)
c = conn.cursor()
c.executescript("""
CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT);
CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL);
CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, total REAL, created_at TEXT);
-- NOTE: intentionally NO index on products.category (that's flaw #3)
CREATE INDEX idx_orders_user ON orders(user_id);
""")

CATS = ["electronics", "books", "home", "toys", "beauty"]
c.executemany("INSERT INTO users(name,email) VALUES(?,?)",
              [(f"User {i}", f"user{i}@ex.com") for i in range(1, 3001)])
c.executemany("INSERT INTO products(name,category,price) VALUES(?,?,?)",
              [(f"Product {i}", random.choice(CATS), round(random.uniform(5, 500), 2))
               for i in range(1, 200001)])
orders = []
for uid in range(1, 3001):
    for _ in range(random.randint(0, 40)):
        orders.append((uid, round(random.uniform(10, 2000), 2), "2026-01-01"))
c.executemany("INSERT INTO orders(user_id,total,created_at) VALUES(?,?,?)", orders)

conn.commit()
print(f"seeded: 500 users, 20000 products, {len(orders)} orders -> {DB}")
conn.close()
