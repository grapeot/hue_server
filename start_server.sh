#!/bin/bash
# Smart Home Dashboard - process launcher entrypoint
# 用法: 由 Background Process Manager / Process Launcher 调用
# 此脚本负责激活环境并启动 Python 服务

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 激活虚拟环境
source "${SCRIPT_DIR}/.venv/bin/activate"

# 环境变量（.env 由 Python load_dotenv() 加载，此处不 source 避免含空格的值被误解析）
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
