# Smart Home Dashboard - Working Log

## Changelog

### 2026-02-18

- **项目初始化**: 合并 hue_server 和 rinnai_heater 到 smart_home
- **添加设备支持**: 集成 Meross 车库门 (MSG200)
- **PRD 文档**: 重写 dev_dashboard.md，定义三个核心功能 (Control/Schedule/History)
- **Shortcut API**: 添加 iOS Shortcut 友好的 Hue 控制接口
- **服务层**: 创建 services/ 目录，封装 Hue/Wemo/Rinnai/Meross 服务
- **API 层**: 创建 api/ 目录，拆分路由模块
- **数据库**: 创建 models/database.py，SQLite 历史数据存储
- **定时任务**: 创建 services/scheduler.py，每30分钟采集状态 + Hue 定时开关
- **main.py 重构**: 整合所有服务层和 API 路由，添加 CORS 和健康检查
- **测试覆盖**: 添加 test/test_hue_service.py, test/test_api.py, test/test_database.py
- **React 前端**: 初始化 Vite + React + TypeScript + TailwindCSS
- **Control Tab**: 设备状态显示和控制按钮
- **Schedule Tab**: Hue/Wemo/Rinnai 定时任务展示
- **History Tab**: Recharts 图表可视化 (亮度/开关/温度)
- **Vite Proxy**: 配置开发时代理到后端
- **UI 中文化**: 全部界面改为中文
- **UI 设计优化**: 渐变背景、圆角卡片、开关按钮样式、响应式布局
- **HistoryTab 修复**: 处理 JSON.parse 错误，支持已解析的数据
- **循环延迟刷新**: 热水器触发循环后10秒再次刷新状态
- **集成测试**: 添加 test/test_integration_real.py，默认跳过
- **PM2 部署**: 添加 ecosystem.config.js，端口 7999
- **生产静态文件**: main.py 自动 serve frontend/dist
- **Rinnai 刷新改造**: 改为复用会话并增加维护刷新接口 `/api/rinnai/maintenance`
- **Rinnai 维护刷新修复**: 刷新改为单请求 `GET /api/status?rinnai_refresh=true`，避免 maintenance + status 双请求导致的错误；修复 popstate 监听（useState→useEffect）
- **Tab URL 路由**: 每个 tab 独立 URL：`/control`、`/schedule`、`/history`，刷新不丢失当前 tab；根路径 `/` 自动替换为 `/control`
- **start_server.sh**: 作为 PM2 的入口脚本（`pm2 start ecosystem.config.js` 时由 PM2 执行），负责激活 venv 并启动 `python main.py`
- **scripts 整理**: introspect_schema.py、create_schedule.py 移至 scripts/；main_legacy.py 删除；test_unit.py 移至 archive/
- **Status API 容错**: 各服务调用加 try/except，单设备不可达时返回 200 + 该设备 error 字段
- **Hue 服务容错**: get_status/turn_on/turn_off/toggle/set_timer 捕获 OSError，离线时返回友好错误；前端 toggleHue 检查 response.status
- **load_dotenv**: main.py 显式指定 `Path(__file__).parent / ".env"`，确保 PM2 环境下正确加载
- **start_server.sh**: 不 source .env（含空格的值如 `Baby room` 会被 shell 误解析为命令）
- **Wemo 配置与调度迁移**: wemo_config.yaml 移至 config/，wemo_schedule.py 移至 services/；更新 main、wemo_service、refresh_wemo_devices 及文档中的路径引用
- **Status API 分解**: `/api/status?devices=hue,wemo,rinnai,garage` 支持按设备拉取，无参数时拉取全部；各设备独立 try-except；前端 toggle 后只 fetch 对应设备
- **维护刷新存库**: 点击「维护刷新」时，Rinnai 状态顺手写入 device_history 表
- **Rinnai 无效数据过滤**: 进水/出水温度为 0 时不存库（可能为 partial failure）；api/status 与 scheduler 均加此逻辑；`scripts/backfill_rinnai_zero_temp.py` 删除已有无效记录
- **History 图表时间轴**: 亮度、热水器温度图改用 XAxis type="number" + dataKey="time"（毫秒时间戳），横轴按实际时间等距显示
- **Security Review**: 新增 docs/SECURITY_REVIEW.md，覆盖隐私暴露、鉴权、输入校验、密钥、网络等
- **安全加固（内网专用）**: 移除 /api/debug；Hue 错误不再返回 bridge_ip；wemo_config.yaml 加入 .gitignore，提供 wemo_config.example.yaml（含内网专用说明）；data/ 加入 .gitignore；history hours 限制 1–168，garage door_index 校验范围

---

## Lessons Learned

### Meross 车库门状态问题
- **问题**: `get_is_open()` 始终返回 True，但实际门是关闭的
- **原因**: MSG200 需要安装磁性传感器才能检测门状态，未安装传感器时无法获取真实状态
- **解决**: API 仅提供触发功能，不显示开/关状态

### Hue Bridge 配对
- **问题**: phue 库首次连接需要按下 Bridge 按钮
- **解决**: 配对信息存储在 `~/.python_hue`，格式为 JSON: `{"192.168.x.x": {"username": "xxx"}}`

### APScheduler 时区
- **问题**: 默认使用 UTC 时区
- **解决**: 显式设置 `timezone=pytz.timezone('America/Los_Angeles')`

### TypeScript type-only import
- **问题**: `error TS1484: 'DeviceStatus' is a type and must be imported using a type-only import`
- **解决**: 使用 `import type { DeviceStatus }` 替代 `import { DeviceStatus }`

### FastAPI 静态文件 SPA
- **问题**: React Router 需要 SPA fallback 到 index.html
- **解决**: 在 main.py 中添加 catch-all 路由，优先检查静态文件，否则返回 index.html

### PM2 与直接运行网络环境不同
- **现象**: 直接 `python main.py` 可连接 Hue Bridge，PM2 下报 No route to host (errno 65)
- **原因**: PM2 进程可能运行在不同机器、不同会话或启动时网络不同（如通过 SSH 在远程启动 PM2）
- **排查**: 直接运行对比；检查 HUE_BRIDGE_IP、网络连通性
- **临时方案**: 用 `screen`/`tmux` 或 `nohup python main.py &` 替代 PM2，或确保 PM2 与终端在同一机器、同一网络

### .env 不要用 shell source
- **问题**: `source .env` 时，`HUE_LIGHT_NAME=Baby room` 中的 `room` 会被解析为命令执行
- **解决**: 由 Python load_dotenv() 加载；main.py 使用 `load_dotenv(Path(__file__).parent / ".env")` 显式路径

### Status API 部分失败
- **问题**: Hue/Wemo 等设备不可达时（如 No route to host），整个 /api/status 返回 500
- **原因**: 聚合接口任一服务抛异常即整体失败
- **解决**: 各服务调用加 try/except，失败时返回该服务的 error 字段，其他服务正常返回；前端 Hue 区显示「离线」状态

### Rinnai API 缓存问题
- **问题**: aiorinnai 库可能缓存 API 连接，导致状态数据不更新
- **现状**: 保持连接 + 失败后重连；通过触发 `/api/rinnai/maintenance` 做“维护读取”后再拉取最新状态

---

## TODO

- [x] 完善 test coverage (api/services)
- [x] 初始化 React + Vite 前端
- [x] 实现 Control Tab
- [x] 实现 Schedule Tab
- [x] 实现 History Tab
- [x] 界面全中文化
- [x] UI 设计优化
- [x] PM2 部署脚本
- [x] 生产环境静态文件 serve
- [x] 集成测试 (skip by default)
- [x] Tab URL 路由 (/control, /schedule, /history)
- [x] Rinnai 维护刷新单请求改造
- [ ] 实际部署到服务器

---

## 部署说明

### 开发模式

```bash
# 后端
cd adhoc_jobs/smart_home
source .venv/bin/activate
python main.py  # 默认端口 7999

# 前端 (另开终端)
cd frontend
npm run dev  # 端口 5173，自动代理 /api 到 7999
```

### 生产模式

```bash
cd adhoc_jobs/smart_home

# 1. 构建前端（首次或前端有更新时）
cd frontend && npm run build && cd ..

# 2. PM2 启动（会执行 start_server.sh）
pm2 start ecosystem.config.js
pm2 save

# 访问 http://localhost:7999
```

### 运行集成测试

```bash
cd adhoc_jobs/smart_home
source .venv/bin/activate
pytest test/test_integration_real.py -m integration
```
