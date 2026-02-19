# Smart Home Dashboard

统一的智能家居控制面板，支持 Hue 灯光、Wemo 开关、Rinnai 热水器、Meross 车库门。内网专用。

## 功能

- **设备控制**：实时查看和控制灯光、开关、热水器、车库门
- **定时任务**：Hue 早晚开关、Wemo 咖啡机定时
- **历史数据**：24 小时内的亮度、开关、温度图表

## 设备支持

| 设备 | 说明 |
|------|------|
| Hue 灯光 | 1 盏，本地 phue API |
| Wemo 开关 | 4 个，SSDP + pywemo |
| Rinnai 热水器 | 云端 aiorinnai，支持循环 |
| Meross 车库门 | 云端 meross-iot |

## 快速开始

### 环境

- Python 3.10+
- Node.js 18+（前端构建）

### 安装

```bash
cd adhoc_jobs/smart_home
python -m venv .venv
source .venv/bin/activate  # 或 Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 配置

1. 复制 `.env.example` 为 `.env`，填入：
   - `HUE_BRIDGE_IP`、`HUE_LIGHT_NAME`
   - `RINNAI_USERNAME`、`RINNAI_PASSWORD`
   - `MEROSS_EMAIL`、`MEROSS_PASSWORD`

2. 复制 `config/wemo_config.example.yaml` 为 `config/wemo_config.yaml`，填入真实设备 IP；或运行 `python scripts/refresh_wemo_devices.py` 自动发现

3. 首次连接 Hue 需按下 Bridge 物理按钮完成配对

### 运行

```bash
# 后端（默认端口 7999）
python main.py

# 前端开发（另开终端）
cd frontend && npm install && npm run dev
```

生产模式：`cd frontend && npm run build` 后，`main.py` 会自动 serve 静态文件。

### PM2 部署

```bash
pm2 start ecosystem.config.js
pm2 save
```

## API 概览

| 路径 | 说明 |
|------|------|
| `GET /api/status` | 设备状态（支持 `?devices=hue,wemo,rinnai,garage`） |
| `GET /api/hue/toggle` | 灯光开关 |
| `GET /api/wemo/{name}/toggle` | Wemo 开关 |
| `GET /api/rinnai/circulate?duration=5` | 热水器循环 |
| `GET /api/status?rinnai_refresh=true` | 维护刷新 + 存库 |
| `GET /api/garage/{n}/toggle` | 车库门 |
| `GET /api/history?hours=24` | 历史数据 |

## 脚本

| 脚本 | 说明 |
|------|------|
| `scripts/refresh_wemo_devices.py` | 发现 Wemo 设备并更新 config |
| `scripts/backfill_rinnai_zero_temp.py` | 删除无效 Rinnai 记录（inlet/outlet 为 0 或 NULL） |
| `scripts/backfill_rinnai_zero_temp.py --dry-run` | 预览将删除的记录 |

## 项目结构

```
smart_home/
├── main.py              # FastAPI 入口
├── api/                 # 路由
├── services/            # Hue/Wemo/Rinnai/Meross 服务
├── models/database.py   # SQLite 历史
├── config/              # wemo_config.yaml（gitignore）
├── frontend/            # React + Vite
└── scripts/             # 工具脚本
```

## 测试

```bash
pytest test/ -v --ignore=test/test_integration_real.py
```

## 文档

- `docs/dev_dashboard.md` - PRD 与功能规格
- `docs/working.md` - 开发日志与 Lessons Learned
