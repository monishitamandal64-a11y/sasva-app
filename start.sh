#!/usr/bin/env bash
# Runs the FastAPI server and the Streamlit client in one container.
set -euo pipefail

PORT="${PORT:-8501}"          # Render injects PORT; Streamlit must bind to it
API_PORT="${API_PORT:-8000}"

echo "Starting SASVA API on :${API_PORT}"
uvicorn server.main:app --host 0.0.0.0 --port "${API_PORT}" --log-level warning &

export SASVA_API_URL="http://localhost:${API_PORT}"

echo "Starting SASVA client on :${PORT}"
exec streamlit run client/app.py \
  --server.port "${PORT}" \
  --server.address 0.0.0.0 \
  --server.headless true
