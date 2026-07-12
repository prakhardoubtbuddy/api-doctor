"""
patient-api — a deliberately slow, partly-insecure API for API Doctor to diagnose.

Six planted flaws (each with a known, reachable fix):
  1. GET /users          N+1 query pattern
  2. GET /orders         no pagination, returns everything
  3. GET /products       missing index on filtered column
  4. GET /reports        blocking synchronous sleep (simulated sync external call)
  5. GET /admin/stats    NO AUTH — security finding
  6. GET /search         expensive aggregation recomputed every call, no cache

Clean endpoints (should pass the 400ms budget, proves the agent doesn't cry wolf):
  GET /health, GET /users/{id}, GET /products/{id}, GET /ping

Run: uvicorn main:app --host 0.0.0.0 --port 8001
"""
import sqlite3, time, os
from fastapi import FastAPI, Header, HTTPException, Query
from contextlib import asynccontextmanager, closing
from datetime import datetime
from typing import Optional

DB = os.path.join(os.path.dirname(__file__), "patient.db")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "api-doctor-secret")
SEARCH_CACHE_TTL_SECONDS = 30
_search_cache = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ = os.path.exists(DB)
    yield


app = FastAPI(title="patient-api", lifespan=lifespan)


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- clean endpoints ----------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ping")
def ping():
    return {"pong": True}


@app.get("/users/{user_id}")
def user_by_id(user_id: int):
    with closing(db()) as conn:
        row = conn.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(404, "user not found")
        return dict(row)


@app.get("/products/{product_id}")
def product_by_id(product_id: int):
    with closing(db()) as conn:
        row = conn.execute("SELECT id, name, category, price FROM products WHERE id = ?", (product_id,)).fetchone()
        if not row:
            raise HTTPException(404, "product not found")
        return dict(row)


# ---------- FLAW 1: N+1 query ----------
@app.get("/users")
def list_users():
    with closing(db()) as conn:
        rows = conn.execute(
            "SELECT u.id, u.name, u.email, COUNT(o.id) order_count, "
            "COALESCE(SUM(o.total), 0) spent FROM users u "
            "LEFT JOIN orders o ON o.user_id = u.id GROUP BY u.id, u.name, u.email"
        ).fetchall()
        return [dict(row) for row in rows]


# ---------- FLAW 2: no pagination ----------
@app.get("/orders")
def list_orders(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    with closing(db()) as conn:
        rows = conn.execute(
            "SELECT id, user_id, total, created_at FROM orders LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------- FLAW 3: missing index ----------
@app.get("/products")
def list_products(
    category: str = "electronics",
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    with closing(db()) as conn:
        rows = conn.execute(
            "SELECT id, name, category, price FROM products "
            "WHERE category = ? LIMIT ? OFFSET ?",
            (category, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------- FLAW 4: blocking sync call ----------
@app.get("/reports")
def reports():
    return {"report": "quarterly", "generated": True}


# ---------- FLAW 5: no auth ----------
@app.get("/admin/stats")
def admin_stats(authorization: Optional[str] = Header(default=None)):
    if authorization != f"Bearer {ADMIN_TOKEN}":
        raise HTTPException(status_code=401, detail="invalid or missing bearer token")
    with closing(db()) as conn:
        u = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
        o = conn.execute("SELECT COUNT(*) c FROM orders").fetchone()["c"]
        rev = conn.execute("SELECT COALESCE(SUM(total),0) s FROM orders").fetchone()["s"]
        return {"users": u, "orders": o, "revenue": rev}


# ---------- FLAW 6: expensive aggregation, no cache ----------
@app.get("/search")
def search(q: str = "a"):
    now = time.monotonic()
    cached = _search_cache.get(q)
    if cached and now - cached[0] < SEARCH_CACHE_TTL_SECONDS:
        return cached[1]
    with closing(db()) as conn:
        rows = conn.execute(
            "SELECT category, COUNT(*) c, AVG(price) avg_price FROM products "
            "WHERE name LIKE ? GROUP BY category", (f"%{q}%",)
        ).fetchall()
        time.sleep(0.6)  # simulate uncached heavy compute
        result = [dict(r) for r in rows]
        _search_cache[q] = (now, result)
        return result
