#!/usr/bin/env bash
# Boots both services on the droplet. Run from repo root.
set -e
pip install -r requirements.txt --break-system-packages -q
( cd patient_api && python3 seed.py && uvicorn main:app --host 0.0.0.0 --port 8001 ) &
( cd control_plane && uvicorn server:app --host 0.0.0.0 --port 8000 ) &
echo "patient-api  -> http://<droplet-ip>:8001  (docs at /docs)"
echo "control+dash -> http://<droplet-ip>:8000"
wait
