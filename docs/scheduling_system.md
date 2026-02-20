# Smart Home - 通用定时任务系统 (PRD + RFC)

> 本文档定义通用定时任务系统，支持自然语言驱动的延迟/定时执行。

---

## 一、背景与目标

### 1.1 问题

现有系统有两套"定时"机制，各有局限：

| 机制 | 实现 | 局限 |
|-----|------|------|
| APScheduler | 固定时间点的 cron 任务 | 只支持预定义任务，运行时无法动态添加 |
| Hue Timer | `asyncio.sleep()` | 仅限 Hue，无法查看任务列表 |

用户需求：
- "6 分钟后关掉圣诞树的灯"
- "30 分钟后触发热水器循环"

### 1.2 目标

构建一个 **General Timing System**，核心抽象：

```
在 [相对时间] 执行 [动作]
```

- **时间**：相对时间（X 分钟/秒后）
- **动作**：结构化描述的 API 调用
- **可视化**：在前端看到所有待执行任务

### 1.3 设计决策

**短时任务不持久化**：
- 这类任务通常几分钟内执行，改动频繁
- 内存存储即可，服务重启丢失是可接受的
- 避免数据库复杂度

---

## 二、概念设计

### 2.1 核心抽象：Scheduled Action

```typescript
interface ScheduledAction {
  id: string;                    // 唯一标识
  action: Action;                // 要执行的动作
  created_at: string;            // 创建时间
  execute_at: string;            // 预计执行时间（ISO 8601）
  minutes: number;               // 延迟分钟数（用于展示）
  status: 'pending' | 'completed' | 'cancelled';
}

interface Action {
  type: string;                  // 动作类型
  params: Record<string, any>;   // 动作参数
}
```

### 2.2 Action 类型定义

| type | params | 说明 |
|------|--------|------|
| `hue.toggle` | `{}` | 切换 Hue 灯 |
| `hue.on` | `{ brightness?: number }` | 开灯 |
| `hue.off` | `{}` | 关灯 |
| `wemo.toggle` | `{ device: string }` | 切换 Wemo 开关 |
| `wemo.on` | `{ device: string }` | 开启 Wemo |
| `wemo.off` | `{ device: string }` | 关闭 Wemo |
| `rinnai.circulate` | `{ duration?: number }` | 触发热水器循环 |
| `garage.toggle` | `{ door: number }` | 触发车库门 |

**示例**：
```json
{
  "type": "wemo.off",
  "params": { "device": "tree" }
}
```

---

## 三、API 设计

### 3.1 创建定时任务

**POST /api/schedule/actions**

Request:
```json
{
  "minutes": 6,
  "action": {
    "type": "wemo.off",
    "params": { "device": "tree" }
  }
}
```

Response:
```json
{
  "id": "abc123",
  "action": { "type": "wemo.off", "params": { "device": "tree" } },
  "minutes": 6,
  "execute_at": "2026-02-19T18:30:00-08:00",
  "created_at": "2026-02-19T18:24:00-08:00",
  "status": "pending"
}
```

### 3.2 查询任务列表

**GET /api/schedule/actions**

Query params:
- `status`: `pending` | `completed` | `cancelled`（可选）

Response:
```json
{
  "actions": [
    {
      "id": "abc123",
      "action": { "type": "wemo.off", "params": { "device": "tree" } },
      "action_display": "关闭 Tree",
      "minutes": 6,
      "execute_at": "2026-02-19T18:30:00-08:00",
      "created_at": "2026-02-19T18:24:00-08:00",
      "status": "pending"
    }
  ]
}
```

### 3.3 取消任务

**DELETE /api/schedule/actions/{id}**

Response:
```json
{
  "id": "abc123",
  "status": "cancelled"
}
```

---

## 四、前端展示（Schedule Tab）

### 4.1 界面设计

在现有 Schedule Tab 底部新增「动态任务」区块：

```
┌─────────────────────────────────────────────────────────────┐
│  ⏰ 动态任务                                                │
│  ─────────────────────────────────────────────────────────  │
│  18:30  关闭 Tree                    [取消]                 │
│  19:00  触发热水器循环 5 分钟         [取消]                 │
│                                                             │
│  共 2 个待执行任务                                           │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 展示字段

| 字段 | 说明 |
|-----|------|
| 执行时间 | `execute_at` 格式化为本地时间（如 18:30） |
| 动作描述 | `action_display`（如"关闭 Tree"） |
| 取消按钮 | 仅 pending 状态显示 |

---

## 五、自然语言接口（OpenCode 集成）

### 5.1 交互流程

```
用户: "6 分钟后关掉圣诞树的灯"
    ↓
OpenCode 解析
    ↓
调用 POST /api/schedule/actions
    ↓
返回确认: "好的，6 分钟后（18:30）关闭 Tree"
```

### 5.2 设备名称映射

```json
{
  "wemo": {
    "coffee": ["coffee", "咖啡机"],
    "veggie": ["veggie", "蔬菜灯"],
    "tree": ["tree", "圣诞树", "圣诞树的灯"],
    "bedroom": ["bedroom", "卧室灯"]
  },
  "hue": ["hue", "baby room", "卧室灯"],
  "rinnai": ["rinnai", "热水器"],
  "garage": ["garage", "车库门"]
}
```

---

## 六、技术实现

### 6.1 架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Schedule Tab)                │
│                      显示动态任务列表                        │
└─────────────────────────┬───────────────────────────────────┘
                          │ GET /api/schedule/actions
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  api/schedule.py                                       │ │
│  │  POST/GET/DELETE /api/schedule/actions                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                          │                                  │
│  ┌───────────────────────┼────────────────────────────────┐│
│  │  services/dynamic_scheduler.py                         ││
│  │  - 内存存储 pending_actions: dict[str, ScheduledAction]││
│  │  - 使用 asyncio.create_task + sleep 实现延时           ││
│  │  - 任务完成/取消后移出 pending，加入 completed 限长队列 ││
│  └───────────────────────┼────────────────────────────────┘│
│                          │                                  │
│  ┌───────────────────────┼────────────────────────────────┐│
│  │  services/action_executor.py                           ││
│  │  - 根据 action.type 路由到对应服务                      ││
│  └───────────────────────┼────────────────────────────────┘│
│                          ▼                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  hue_service / wemo_service / rinnai_service / ...     │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Action Executor

```python
ACTION_HANDLERS = {
    'hue.toggle': lambda: hue_service.toggle(),
    'hue.on': lambda p: hue_service.turn_on(p.get('brightness', 128)),
    'hue.off': lambda: hue_service.turn_off(),
    'wemo.toggle': lambda p: wemo_service.toggle(p['device']),
    'wemo.on': lambda p: wemo_service.turn_on(p['device']),
    'wemo.off': lambda p: wemo_service.turn_off(p['device']),
    'rinnai.circulate': lambda p: asyncio.run(rinnai_service.circulate(p.get('duration', 5))),
    'garage.toggle': lambda p: asyncio.run(meross_service.toggle_door(p['door'])),
}
```

### 6.3 文件结构

```
services/
├── dynamic_scheduler.py   # 新增：动态任务管理（内存存储）
├── action_executor.py     # 新增：动作执行器
├── scheduler.py           # 现有：固定任务（保持不变）
└── ...

api/
├── schedule.py            # 新增：定时任务 API
└── ...
```

---

## 七、实施计划

### Phase 1: 后端核心（1 天）

1. `services/action_executor.py` - 动作执行器
2. `services/dynamic_scheduler.py` - 动态调度器
3. `api/schedule.py` - REST API
4. 测试覆盖

### Phase 2: 前端展示（0.5 天）

1. 在 Schedule Tab 显示动态任务
2. 支持取消任务

### Phase 3: OpenCode 集成（0.5 天）

1. 整理设备清单
2. 测试自然语言交互

---

## 八、使用示例

### 通过 API

```bash
# 6 分钟后关闭圣诞树灯
curl -X POST http://localhost:7999/api/schedule/actions \
  -H "Content-Type: application/json" \
  -d '{"minutes": 6, "action": {"type": "wemo.off", "params": {"device": "tree"}}}'

# 查看待执行任务
curl http://localhost:7999/api/schedule/actions?status=pending

# 取消任务
curl -X DELETE http://localhost:7999/api/schedule/actions/abc123
```

### 通过自然语言（OpenCode）

```
用户: "6 分钟后关掉圣诞树的灯"
OpenCode: "好的，6 分钟后（18:30）关闭 Tree"

用户: "还有哪些待执行的任务？"
OpenCode: "目前有 2 个待执行任务..."
```
