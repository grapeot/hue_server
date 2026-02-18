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
- **Rinnai 缓存修复**: 每次获取状态重新登录以获取最新数据

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

### Rinnai API 缓存问题
- **问题**: aiorinnai 库可能缓存 API 连接，导致状态数据不更新
- **解决**: 每次获取状态时重新登录创建新 API session

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
# 1. 构建前端
cd adhoc_jobs/smart_home/frontend
npm run build

# 2. PM2 启动
cd adhoc_jobs/smart_home
pm2 start ecosystem.config.js
pm2 save

# 3. 访问
# http://localhost:7999
```

### 运行集成测试

```bash
cd adhoc_jobs/smart_home
source .venv/bin/activate
pytest test/test_integration_real.py -m integration
```
