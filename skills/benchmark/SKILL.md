# Skill: benchmark

Measure every endpoint of the target API against a 400ms budget and audit auth.

## Inputs
- BASE_URL of the patient API (e.g. http://127.0.0.1:8001)
- CONTROL_URL of the control plane (e.g. http://127.0.0.1:8000)
- RUN_ID (create one first via POST {CONTROL_URL}/api/runs)
- PHASE: "before" or "after"

## Steps
1. Discover routes: read the patient API's OpenAPI at {BASE_URL}/openapi.json. List every GET path. For paths with {id}, use id=1.
2. For each route, call it 20 times. Record response times, take the p95 (95th percentile). Record the payload size in KB from the largest response.
3. Auth audit: for each route, also call it with NO Authorization header. If a route under /admin (or any route you judge sensitive) returns HTTP 200 without a token, set auth_ok=false.
4. Decide status per endpoint:
   - "fail_auth" if auth_ok is false
   - else "fail_latency" if p95 > 400
   - else "pass"
5. POST each result to {CONTROL_URL}/api/endpoints with:
   {run_id, path, method, phase, p95_ms, payload_kb, auth_ok, status}

## Rules
- Never trust a single call; p95 over 20 is the metric.
- Report numbers exactly; do not round away a violation.
