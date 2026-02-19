#!/bin/bash
# Smart Home Dashboard - 由 PM2 启动的入口脚本
# 用法: pm2 start ecosystem.config.js
# 此脚本负责激活环境并启动 Python 服务

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 激活虚拟环境
source "${SCRIPT_DIR}/.venv/bin/activate"

# 环境变量（可被 ecosystem.config.js 的 env 覆盖）
export PORT="${PORT:-7999}"

exec python main.py
