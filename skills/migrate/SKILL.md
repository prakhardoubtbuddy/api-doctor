# Skill: migrate (Migrate / Modernize mode)

API Doctor's second mode. Take an organization's existing codebase and bring it
UP TO DATE by editing it IN PLACE — never a rewrite. Use when the user wants to
migrate or modernize a whole application, not just fix performance.

## Inputs
- REPO path (e.g. ~/api-doctor/patient_api)
- CONTROL_URL of the control-plane
- RUN_ID (create one first via POST {CONTROL_URL}/api/runs)

## Steps
1. INVENTORY: read the repo. Identify framework/version, language version, deps.
   List every deprecated/outdated pattern. Common targets:
   - @app.on_event("startup"/"shutdown") -> lifespan context-manager pattern
   - datetime.utcnow() -> datetime.now(timezone.utc)
   - Query(..., regex=...) -> Query(..., pattern=...)
   - sync handlers doing blocking I/O -> async / offload
   - end-of-life dependency pins -> bump
2. PLAN: ordered, in-place, individually-verifiable, revertible changes. POST each
   to {CONTROL_URL}/api/findings as {run_id, endpoint, type:"deprecated_pattern",
   code_location, proposed_fix, status:"found"}.
3. APPLY on branch api-doctor/modernize, ONE change per commit.
4. VERIFY after each: app still starts, endpoints return the same shape. When ok,
   PATCH {CONTROL_URL}/api/findings {run_id, type, status:"verified"}.
5. QUARANTINE ambiguous changes — flag for a human, never guess a behavior change.
6. Open ONE PR "Modernize <repo>: <n> changes" with a checklist body; PATCH run pr_url.

## Hard rules
- Preserve behavior. Changed outputs = bug, not feature.
- No rewrites. Edit what exists.
- Every change revertible on its own commit.
- Prove the app still works before marking done.
