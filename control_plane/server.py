"""
control-plane — the API Doctor backend + dashboard.
Holds runs / endpoints / findings. The Hermes agent POSTs results here; the
dashboard polls GET endpoints. Single SQLite file, no external services.

Run: uvicorn server:app --host 0.0.0.0 --port 8000
Dashboard: http://<droplet-ip>:8000/
"""
import sqlite3, os, json, time
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

DB = os.path.join(os.path.dirname(__file__), "doctor.db")
HERE = os.path.dirname(__file__)
app = FastAPI(title="api-doctor-control-plane")


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY, repo_url TEXT, status TEXT,
            started_at REAL, pr_url TEXT);
        CREATE TABLE IF NOT EXISTS endpoints (
            id INTEGER PRIMARY KEY, run_id INTEGER, path TEXT, method TEXT,
            phase TEXT, p95_ms REAL, payload_kb REAL, auth_ok INTEGER, status TEXT);
        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY, run_id INTEGER, endpoint TEXT, type TEXT,
            code_location TEXT, proposed_fix TEXT, status TEXT);
        """)


init()


# ---------- agent writes here ----------
@app.post("/api/runs")
async def create_run(req: Request):
    b = await req.json()
    with db() as conn:
        cur = conn.execute("INSERT INTO runs(repo_url,status,started_at) VALUES(?,?,?)",
                           (b.get("repo_url", ""), "running", time.time()))
        return {"run_id": cur.lastrowid}


@app.patch("/api/runs/{run_id}")
async def update_run(run_id: int, req: Request):
    b = await req.json()
    with db() as conn:
        for k in ("status", "pr_url"):
            if k in b:
                conn.execute(f"UPDATE runs SET {k}=? WHERE id=?", (b[k], run_id))
    return {"ok": True}


@app.post("/api/endpoints")
async def upsert_endpoint(req: Request):
    b = await req.json()
    with db() as conn:
        conn.execute(
            "INSERT INTO endpoints(run_id,path,method,phase,p95_ms,payload_kb,auth_ok,status) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (b["run_id"], b["path"], b.get("method", "GET"), b.get("phase", "before"),
             b.get("p95_ms"), b.get("payload_kb"), int(b.get("auth_ok", 1)), b.get("status")))
    return {"ok": True}


@app.post("/api/findings")
async def add_finding(req: Request):
    b = await req.json()
    with db() as conn:
        conn.execute(
            "INSERT INTO findings(run_id,endpoint,type,code_location,proposed_fix,status) "
            "VALUES(?,?,?,?,?,?)",
            (b["run_id"], b["endpoint"], b["type"], b.get("code_location", ""),
             b.get("proposed_fix", ""), b.get("status", "found")))
    return {"ok": True}


@app.patch("/api/findings")
async def update_finding(req: Request):
    b = await req.json()
    with db() as conn:
        conn.execute("UPDATE findings SET status=? WHERE run_id=? AND type=?",
                     (b["status"], b["run_id"], b["type"]))
    return {"ok": True}


# ---------- dashboard reads here ----------
@app.get("/api/state/{run_id}")
def state(run_id: int):
    with db() as conn:
        run = conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        eps = conn.execute("SELECT * FROM endpoints WHERE run_id=? ORDER BY path", (run_id,)).fetchall()
        fs = conn.execute("SELECT * FROM findings WHERE run_id=?", (run_id,)).fetchall()
        return {"run": dict(run) if run else None,
                "endpoints": [dict(e) for e in eps],
                "findings": [dict(f) for f in fs]}


@app.get("/api/latest")
def latest():
    with db() as conn:
        r = conn.execute("SELECT id FROM runs ORDER BY id DESC LIMIT 1").fetchone()
        return {"run_id": r["id"] if r else None}


@app.get("/")
def index():
    return FileResponse(os.path.join(HERE, "static", "index.html"))
