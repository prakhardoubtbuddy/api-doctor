#!/usr/bin/env bash
set -e
REPO=~/api-doctor
CONTROL=http://127.0.0.1:8000
PATIENT=http://127.0.0.1:8001
echo "=== API Doctor demo reset ==="
fuser -k 8001/tcp 2>/dev/null || true
sleep 1
cd "$REPO"
git checkout main -q
git branch -D api-doctor/autofix 2>/dev/null || true
cd "$REPO/patient_api"
python3 seed.py
nohup uvicorn main:app --host 0.0.0.0 --port 8001 > ~/patient.log 2>&1 &
sleep 4
if ! curl -fsS "$CONTROL/api/latest" >/dev/null 2>&1; then
  cd "$REPO/control_plane"
  nohup uvicorn server:app --host 0.0.0.0 --port 8000 > ~/control.log 2>&1 &
  sleep 3
fi
echo
echo "=== patient vitals (should be SLOW / unprotected) ==="
printf "  /reports   : "; curl -s -o /dev/null -w "%{time_total}s (expect ~1.5s)\n"  "$PATIENT/reports"
printf "  /admin no-token HTTP: "; curl -s -o /dev/null -w "%{http_code} (expect 200 = exposed)\n" "$PATIENT/admin/stats"
echo
echo "=== ready — open the dashboard, start hermes, paste the demo command ==="
