# API Doctor

An autonomous agent that diagnoses any organization's API: it benchmarks every
endpoint against a 400ms budget, audits authentication, scans the code for
inefficiencies, then **writes the fixes, opens a PR, redeploys, and re-benchmarks
to prove the improvement** — with a live red-to-green dashboard.

Built for the Hermes Agent Buildathon. Stack: OpenAI key + Hermes + one DigitalOcean droplet.

## Layout
- `patient_api/`   — a deliberately slow/insecure demo API with 6 planted flaws
- `control_plane/` — findings DB + live dashboard (FastAPI, port 8000)
- `skills/`        — Hermes skills: benchmark, code-scan, fix-and-verify, pitfalls

## Run (on the droplet)
```bash
./run_all.sh
# patient-api  : http://<ip>:8001/docs
# dashboard    : http://<ip>:8000
```

## The agent loop (Hermes)
1. create a run:  POST /api/runs
2. `benchmark` skill  (phase=before) -> endpoint rows appear on the dashboard
3. `code-scan` skill  -> findings appear
4. `fix-and-verify` skill -> applies fixes, opens PR, redeploys, benchmark (phase=after)
5. dashboard flips red -> green; `pitfalls/SKILL.md` gets the lessons

## Generalize beyond the demo
The agent is org-agnostic — point it at any repo URL. The patient API is just a
known-good demo target so the flip is deterministic on stage.
