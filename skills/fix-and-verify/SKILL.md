# Skill: fix-and-verify

Apply the fixes, open a PR, redeploy, and re-benchmark to prove improvement.

## Steps
1. Create a git branch: api-doctor/autofix-{RUN_ID}.
2. For each finding with status "found", edit the patient_api source to apply the
   proposed_fix from the code-scan skill. Keep each fix minimal and correct:
   - n_plus_one -> single JOIN with GROUP BY
   - no_pagination -> add limit/offset params
   - missing_index -> add CREATE INDEX to seed/schema and re-run it
   - blocking_io -> remove sleep / make async
   - no_auth -> add token check returning 401
   - no_cache -> add a small TTL cache
   After each edit, PATCH {CONTROL_URL}/api/findings {run_id, type, status:"fixed"}.
3. Commit, push the branch, open a PR via the GitHub API. PATCH the run with pr_url.
4. Restart the patient API so the fixes are live (re-run seed if the index changed).
5. Re-run the benchmark skill with PHASE="after".
6. For every finding whose endpoint now passes, PATCH status:"verified".
7. Write a one-line summary of before vs after p95 per endpoint.

## Rule
Only mark "verified" when the after-benchmark actually passes. No wishful status.
