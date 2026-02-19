#!/bin/bash
# Smart Home Dashboard - PM2 启动脚本
# 用法: ./start_server.sh [build]
# 带 build 参数时会先构建前端

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ "$1" = "build" ]; then
  echo "Building frontend..."
  (cd frontend && npm run build)
  echo "Frontend built."
fi

if [ ! -d "frontend/dist" ]; then
  echo "Warning: frontend/dist not found. Run with 'build' to build first, or start in dev mode."
fi

echo "Starting with PM2..."
pm2 start ecosystem.config.js
echo "Started. Run 'pm2 logs smart-home' to view logs, 'pm2 stop smart-home' to stop."
