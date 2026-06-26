#!/bin/bash
# Smart Home Dashboard - process launcher entrypoint
# Called by Background Process Manager / Process Launcher.
# Activates the environment and starts the Python service.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment.
source "${SCRIPT_DIR}/.venv/bin/activate"

# Python load_dotenv() reads .env; do not source it because values may contain spaces.
export PORT="${PORT:-7999}"

RESEND_API_KEY_VALUE="$(python - <<'PY'
from pathlib import Path

from dotenv import dotenv_values

env_path = Path(".env")
if env_path.exists():
    print(dotenv_values(env_path).get("RESEND_API_KEY") or "")
PY
)"

if [[ "${RESEND_API_KEY_VALUE}" == op://* ]] && command -v op >/dev/null 2>&1; then
    export RESEND_API_KEY="$(op read "${RESEND_API_KEY_VALUE}")"
fi

exec python main.py
