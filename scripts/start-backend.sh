#!/bin/bash
# Start backend in development mode with --reload.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

source "${PROJECT_ROOT}/.venv/bin/activate"
export PORT="${PORT:-7999}"
export SMART_HOME_BIND_HOSTS="${SMART_HOME_BIND_HOSTS:-127.0.0.1}"

exec uvicorn main:app --reload --host 127.0.0.1 --port "$PORT"
