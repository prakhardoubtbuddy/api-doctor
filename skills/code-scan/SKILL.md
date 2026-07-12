# Skill: code-scan

Read the patient API source and find the six inefficiency/security patterns.
For each one found, POST a finding to {CONTROL_URL}/api/findings.

## Patterns to detect (with the fix you will propose)
1. n_plus_one — a DB query inside a loop over rows.
   Fix: replace with a single JOIN + GROUP BY.
2. no_pagination — a list endpoint with SELECT ... with no LIMIT/OFFSET.
   Fix: add limit & offset query params, default limit 100.
3. missing_index — a WHERE filter on a column that has no CREATE INDEX.
   Fix: add an index on that column in the schema.
4. blocking_io — time.sleep or a synchronous blocking call in a handler.
   Fix: make the endpoint async / offload; remove the blocking sleep.
5. no_auth — a sensitive route (e.g. /admin/*) with no token check.
   Fix: add an Authorization header check that returns 401 when missing.
6. no_cache — an expensive aggregation recomputed every call.
   Fix: add an in-memory TTL cache keyed by the query params.

## Steps
1. Read every .py file in the patient_api directory.
2. For each pattern above that you find, POST:
   {run_id, endpoint, type, code_location (file:line), proposed_fix, status:"found"}
3. Do NOT invent findings. Only report patterns you can point to a line for.
