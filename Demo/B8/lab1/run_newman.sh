#!/usr/bin/env bash
set -euo pipefail

# Ensure working directory is lab1
cd "$(dirname "$0")"

# 1. Check/create instance dir for SQLite
mkdir -p instance

# 2. Check and start server in background if not already listening
if ! ss -tulpn 2>/dev/null | grep -q ":5000 "; then
  echo "[+] Starting Flask API in background..."
  .venv/bin/python app.py --port 5000 >/dev/null 2>&1 &
  SERVER_PID=$!
  trap 'kill $SERVER_PID 2>/dev/null || true' EXIT
  sleep 1
else
  echo "[+] Server already running on port 5000."
fi

# 3. Verify health
curl -sf http://127.0.0.1:5000/health > /dev/null || {
  echo "[-] Health check failed"
  exit 1
}

# 4. Run Newman
echo "[+] Running Newman test suite..."
newman run postman/books-api.postman_collection.json \
  -e postman/local.postman_environment.json \
  -r cli,junit \
  --reporter-junit-export junit.xml

echo "[+] Newman run finished successfully. JUnit exported to junit.xml"
