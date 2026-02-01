#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="/home/grapeot/co/hue_server"

# 激活Python虚拟环境
source "${SCRIPT_DIR}/py310/bin/activate"

# 设置 Hue Bridge IP
export HUE_BRIDGE_IP="192.168.180.123"

# 启动服务器
exec python "${SCRIPT_DIR}/main.py"
