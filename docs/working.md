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

---

## TODO

- [ ] 完善 test coverage (api/services)
- [ ] 初始化 React + Vite 前端
- [ ] 实现 Control Tab
- [ ] 实现 Schedule Tab
- [ ] 实现 History Tab
- [ ] 集成测试
