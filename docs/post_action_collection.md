# Smart Home - 控制后延迟采集系统 (PRD + RFC)

> 本文档定义控制后延迟采集系统，在 API 控制设备后自动延迟采集状态并存入数据库。

---

## 一、背景与目标

### 1.1 问题

现有系统的状态采集机制：

| 机制 | 频率 | 问题 |
|-----|------|------|
| 定时采集 | 每 30 分钟 | 间隔太长，控制操作后状态变化无法被记录 |
| 前端 10 秒延迟 | 仅前端刷新 | 只更新 UI，不写入数据库 |

用户控制设备后（如开灯、触发热水器循环），状态变化要等 30 分钟才会被记录，导致历史数据不完整。

### 1.2 目标

构建一个 **Post-Action Collection System**，核心抽象：

```
执行 [控制操作] → 等待 [延迟时间] → 采集 [目标设备状态] → 存入数据库
```

- **自动化**：无需手动触发，控制操作自动触发采集
- **精确采集**：只采集相关设备，不做全量采集
- **最小成本**：延迟采集避免频繁 API 调用，与现有 30 分钟采集互补

### 1.3 设计决策

**复用现有架构**：
- 使用 `asyncio.create_task` + `asyncio.sleep` 实现延迟（类似 dynamic_scheduler）
- 复用 `models/database.py` 的 `save_device_state` 存库
- 复用各 `services/xxx_service.py` 的 `get_status` 方法

**前端 10 秒延迟保持不变**：
- 前端的 `setTimeout` 只更新 UI，与后端采集独立
- 后端采集时间可配置，默认 10 秒

---

## 二、概念设计

### 2.1 操作类型到采集内容的映射

| 设备 | 操作类型 | 采集内容 | 说明 |
|------|---------|---------|------|
| Hue | toggle, on, off | `is_on`, `brightness` | 开关状态 + 亮度 |
| Wemo | toggle, on, off | `is_on` | 开关状态 |
| Rinnai | circulate | `set_temperature`, `inlet_temp`, `outlet_temp`, `water_flow`, `recirculation_enabled` | 完整温度数据 |
| Garage | toggle | 无 | 无传感器，不采集 |

### 2.2 采集延迟配置

| 设备 | 默认延迟 | 理由 |
|------|---------|------|
| Hue | 3 秒 | 本地 API，响应快 |
| Wemo | 3 秒 | 本地 SSDP，响应快 |
| Rinnai | 10 秒 | 云端 API，需要时间生效 |
| Garage | - | 不采集 |

### 2.3 核心流程

```
用户调用控制 API (如 /api/hue/toggle)
    ↓
API 执行控制操作
    ↓
调用 post_action_collector.schedule_collection(device_type, device_name, delay_seconds)
    ↓
返回 API 响应给用户（不等待采集）
    ↓
[后台] asyncio.create_task 启动延迟采集任务
    ↓
[延迟后] 调用 service.get_status() 获取状态
    ↓
调用 save_device_state() 存入数据库
```

---

## 三、API 设计

### 3.1 内部接口（非 HTTP）

`services/post_action_collector.py` 提供内部接口，供 API 层调用：

```python
async def schedule_collection(
    device_type: str,      # 'hue', 'wemo', 'rinnai'
    device_name: str,      # 'baby_room', 'coffee', 'main_house'
    delay_seconds: float = 10.0
) -> None:
    """
    安排延迟采集任务。
    不返回结果，完全异步执行。
    """
```

### 3.2 使用示例

在 `api/hue.py` 中：

```python
from services.post_action_collector import schedule_collection

@router.get("/toggle")
async def hue_toggle():
    result = hue_service.toggle()
    # 安排 3 秒后采集状态
    await schedule_collection("hue", "baby_room", delay_seconds=3)
    return result
```

在 `api/rinnai.py` 中：

```python
@router.get("/circulate")
async def rinnai_circulate(duration: int = 5):
    result = await rinnai_service.start_circulation(duration)
    # 安排 10 秒后采集状态
    await schedule_collection("rinnai", "main_house", delay_seconds=10)
    return result
```

---

## 四、技术实现

### 4.1 架构

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI API Layer                      │
│  api/hue.py, api/wemo.py, api/rinnai.py                     │
│                          │                                  │
│          调用 schedule_collection()                         │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│            services/post_action_collector.py                │
│  - schedule_collection(): 创建 asyncio.Task                 │
│  - _collect_and_save(): 延迟后执行采集+存库                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ hue_service  │ │ wemo_service │ │rinnai_service│
│ .get_status()│ │.get_status() │ │.get_status() │
└──────────────┘ └──────────────┘ └──────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                models/database.py                           │
│                save_device_state()                          │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 文件结构

```
services/
├── post_action_collector.py   # 新增：控制后延迟采集
├── dynamic_scheduler.py       # 现有：动态任务（保持不变）
├── action_executor.py         # 现有：动作执行器（保持不变）
├── scheduler.py               # 现有：固定任务（保持不变）
└── ...

api/
├── hue.py                     # 修改：添加采集调用
├── wemo.py                    # 修改：添加采集调用
├── rinnai.py                  # 修改：添加采集调用
└── ...
```

### 4.3 实现细节

**延迟采集逻辑**：
1. 使用 `asyncio.create_task` 创建后台任务
2. 任务内部 `await asyncio.sleep(delay_seconds)`
3. 调用对应 service 的 `get_status()` 方法
4. 调用 `save_device_state()` 存库
5. 异常捕获并记录日志，不影响主流程

**去重与合并**：
- 如果短时间内多次控制同一设备，每个控制操作独立触发采集
- 不做任务合并（简单实现）
- 多次采集会写入多条记录（符合历史数据语义）

---

## 五、与现有系统的关系

### 5.1 与定时采集的关系

| 特性 | 定时采集 | 控制后采集 |
|-----|---------|-----------|
| 触发方式 | 时间驱动 | 事件驱动 |
| 频率 | 固定 30 分钟 | 按需触发 |
| 采集范围 | 所有设备 | 单个设备 |
| 数据覆盖 | 基础覆盖 | 补充覆盖 |

两者互补，共同提供更完整的历史数据。

### 5.2 与前端 10 秒延迟的关系

| 特性 | 前端 10 秒延迟 | 后端延迟采集 |
|-----|---------------|-------------|
| 目的 | 刷新 UI | 记录历史 |
| 执行位置 | 浏览器 | 服务器 |
| 数据去向 | 前端状态 | 数据库 |
| 是否需要修改 | 否 | 否 |

两者独立，不需要修改前端代码。

---

## 六、实施计划

### Phase 1: 后端核心（0.5 天）

1. 创建 `services/post_action_collector.py`
2. 修改 `api/hue.py`、`api/wemo.py`、`api/rinnai.py`
3. 单元测试

### Phase 2: 集成测试（0.5 天）

1. 端到端测试
2. 验证数据库记录
3. 更新文档

---

## 七、使用示例

### 7.1 开灯后采集亮度

```bash
# 用户调用 API
curl http://localhost:7999/api/hue/toggle

# 3 秒后，后端自动采集并存库
# 数据库新增记录：
# device_type: hue
# device_name: baby_room
# data: {"is_on": true, "brightness": 128}
```

### 7.2 热水器循环后采集温度

```bash
# 用户调用 API
curl http://localhost:7999/api/rinnai/circulate?duration=5

# 10 秒后，后端自动采集并存库
# 数据库新增记录：
# device_type: rinnai
# device_name: main_house
# data: {"set_temperature": 125, "inlet_temp": 103, "outlet_temp": 121, ...}
```

---

## 八、配置参数

| 参数 | 默认值 | 说明 |
|-----|-------|------|
| HUE_COLLECT_DELAY | 3 | Hue 采集延迟（秒） |
| WEMO_COLLECT_DELAY | 3 | Wemo 采集延迟（秒） |
| RINNAI_COLLECT_DELAY | 10 | Rinnai 采集延迟（秒） |

可通过环境变量覆盖。
