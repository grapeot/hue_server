#!/bin/bash
# Smart Home Dashboard - 由 PM2 启动的入口脚本
# 用法: pm2 start ecosystem.config.js
# 此脚本负责激活环境并启动 Python 服务

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 激活虚拟环境
source "${SCRIPT_DIR}/.venv/bin/activate"

# 环境变量（.env 由 Python load_dotenv() 加载，此处不 source 避免含空格的值被误解析）
export PORT="${PORT:-7999}"

exec python main.py
