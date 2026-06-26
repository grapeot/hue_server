# Smart Home Dashboard - PRD + RFC

> 本文档是产品需求文档 (PRD) 和技术方案 (RFC) 的合体，定义四个核心功能模块及其实现方案。

---

## 一、产品概述

### 1.1 目标

构建一个统一的 Smart Home 控制面板，提供：
1. **设备控制**: 实时查看和控制所有智能家居设备
2. **监控预览**: 实时查看所有摄像头画面（按需抓取）
3. **定时任务**: 可视化展示所有定时任务
4. **历史数据**: 记录并可视化设备状态历史

### 1.2 已集成设备

| 设备类型 | 数量 | API | 备注 |
|---------|------|-----|------|
| Hue 灯光 | 1 盏 (Baby room) | 本地 API (phue) | 主要控制目标 |
| Wemo 开关 | 4 个 | SSDP + UPnP (pywemo) | Coffee, Veggie, Tree, Bedroom |
| Rinnai 热水器 | 1 台 | 云端 GraphQL (aiorinnai) | 支持循环模式 |
| Meross 车库门 | 2 门 | 本地 HTTP `/config` + Meross 签名 | 无传感器，仅触发控制；可选邮件通知 |
| Amcrest 摄像头 | 8 个 | 本地 HTTP (Digest Auth) | 按需抓取，不做存储 |

---

## 二、功能需求

### 2.1 Tab 1: Control（设备控制）

#### 2.1.1 界面设计

```
┌─────────────────────────────────────────────────────────────┐
│  [Control]  [Cameras]  [Schedule]  [History]                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  💡 灯光                                                 ││
│  │  ─────────────────────────────────────────────────────  ││
│  │  Baby Room     [====●===========] 亮度: 128  [开关]     ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  🔌 开关                                                 ││
│  │  ─────────────────────────────────────────────────────  ││
│  │  Coffee        [● ON]     [切换]                        ││
│  │  Veggie        [● ON]     [切换]                        ││
│  │  Tree          [○ OFF]    [切换]                        ││
│  │  Bedroom       [○ OFF]    [切换]                        ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  🚿 热水器                                               ││
│  │  ─────────────────────────────────────────────────────  ││
│  │  Main House   温度: 125°F  状态: ● 在线                  ││
│  │                进水: 103°F  出水: 121°F                  ││
│  │                [触发5分钟循环]                            ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  🚗 车库门                                               ││
│  │  ─────────────────────────────────────────────────────  ││
│  │  Garage Door 1     [触发开关]                            ││
│  │  Garage Door 2     [触发开关]                            ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 2.1.2 功能规格

**Hue (Baby Room)**
| 操作 | 行为 |
|-----|------|
| 显示 | 当前状态 (ON/OFF) + 亮度 (0-254) |
| 点击开关 | Flip: ON→OFF 或 OFF→ON (亮度保持) |

**Wemo (4个开关)**
| 操作 | 行为 |
|-----|------|
| 显示 | 当前状态 (ON/OFF) |
| 点击切换 | Flip: ON→OFF 或 OFF→ON |

**Rinnai 热水器**
| 操作 | 行为 |
|-----|------|
| 显示 | 设定温度、进水温度、出水温度、在线状态 |
| 点击触发 | 启动 5 分钟循环模式 |

**Meross 车库门**
| 操作 | 行为 |
|-----|------|
| 显示 | 仅名称，无状态（传感器未安装） |
| 点击触发 | Toggle: POST 到后端，后端通过 Meross 本地 HTTP `/config` 发送开关信号 |
| 触发后通知 | 可选：若启用 Resend 配置，向配置收件人发送邮件通知 |

---

### 2.2 Tab 2: Cameras（监控预览）

#### 2.2.1 界面设计

```
┌─────────────────────────────────────────────────────────────┐
│  [Control]  [Cameras]  [Schedule]  [History]                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐│
│  │  📷 实时监控                          [刷新全部] [加载中]││
│  ─────────────────────────────────────────────────────────  ││
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Upstairs Patio                                           ││
│  │ ┌─────────────────────────────────────────────────────┐ ││
│  │ │                                                     │ ││
│  │ │              [缩略图预览]                            │ ││
│  │ │                                                     │ ││
│  │ └─────────────────────────────────────────────────────┘ ││
│  │                                    点击查看全分辨率 →    ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Frontyard                                                ││
│  │ ┌─────────────────────────────────────────────────────┐ ││
│  │ │                                                     │ ││
│  │ │              [缩略图预览]                            │ ││
│  │ │                                                     │ ││
│  │ └─────────────────────────────────────────────────────┘ ││
│  │                                    点击查看全分辨率 →    ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ... (每个摄像头一行)                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘

全分辨率弹窗:
┌─────────────────────────────────────────────────────────────┐
│  Frontyard - 全分辨率                           [X 关闭]   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐│
│  │                                                         ││
│  │                                                         ││
│  │                  [全分辨率图片]                          ││
│  │                                                         ││
│  │                                                         ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

#### 2.2.2 功能规格

**核心行为**
- **按需抓取**: 用户进入 Cameras Tab 时才开始抓取，不预先缓存
- **异步并行**: 所有摄像头同时发起请求，不阻塞 UI
- **无存储**: 图片不落盘，直接 proxy 返回前端
- **无周期性刷新**: 不自动刷新，用户手动点击"刷新全部"或单个刷新

**摄像头列表**
| 名称 | IP | 状态 |
|-----|-----|------|
| Upstairs Patio | 192.0.2.20 | 待实现 |
| Frontyard | 192.0.2.21 | 待实现 |
| Outer Patio | 192.0.2.22 | 待实现 |
| Backyard | 192.0.2.23 | 待实现 |
| Heat Pump Side Door | 192.0.2.24 | 待实现 |
| Downstairs Side Door | 192.0.2.25 | 待实现 |
| Driveway | 192.0.2.26 | 待实现 |
| Babyroom | 192.0.2.27 | 待实现 |

**交互规格**
| 操作 | 行为 |
|-----|------|
| 进入 Tab | 显示所有摄像头，立即异步抓取所有图片 |
| 点击缩略图 | 弹窗显示全分辨率图片（重新请求一次） |
| 点击"刷新全部" | 重新抓取所有摄像头 |
| 单个刷新 | 重新抓取该摄像头 |
| 加载中状态 | 显示 loading 占位图 |
| 加载失败 | 显示错误占位图 + 重试按钮 |

---

### 2.3 Tab 3: Schedule（定时任务）

#### 2.3.1 界面设计

```
┌─────────────────────────────────────────────────────────────┐
│  [Control]  [Cameras]  [Schedule]  [History]                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  💡 Hue 定时任务                                         ││
│  │  ─────────────────────────────────────────────────────  ││
│  │  每天 20:00   开灯 (亮度 128)                            ││
│  │  每天 08:20   关灯                                       ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  🔌 Wemo 定时任务                                        ││
│  │  ─────────────────────────────────────────────────────  ││
│  │  Coffee  每天 07:45   开启                               ││
│  │  Coffee  每天 11:00   关闭                               ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  🚿 热水器定时任务 (来自设备)                             ││
│  │  ─────────────────────────────────────────────────────  ││
│  │  MorningShower   07:30-08:15   每天                      ││
│  │  AfternoonPeak   16:30-18:00   每天                      ││
│  │  NightShower     20:30-23:00   每天                      ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 2.3.2 功能规格

**后端新增定时任务**

| 设备 | 时间 (PT) | 操作 | 实现 |
|-----|----------|------|------|
| Hue Baby Room | 每天 20:00 | 开灯，亮度设为 128 | APScheduler |
| Hue Baby Room | 每天 08:20 | 关灯 | APScheduler |
| Wemo (现有) | 按 config/wemo_config.yaml | 开/关 | APScheduler (已有) |

**热水器 Schedule**
- 从 Rinnai API 读取现有 schedule（只读展示）
- 不在后端管理，仅前端展示

---

### 2.4 Tab 4: History（历史数据）

#### 2.4.1 界面设计

```
┌─────────────────────────────────────────────────────────────┐
│  [Control]  [Cameras]  [Schedule]  [History]                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  💡 Baby Room 亮度 (24小时)                              ││
│  │  ─────────────────────────────────────────────────────  ││
│  │  [折线图: 亮度 vs 时间]                                   ││
│  │  平均亮度: 128  最高: 254  最低: 0                       ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  🔌 Wemo 开关状态 (24小时)                               ││
│  │  ─────────────────────────────────────────────────────  ││
│  │  [时间线图: ON/OFF 状态变化]                              ││
│  │                                                          ││
│  │  开启时长统计:                                            ││
│  │  Coffee    ████████ 8小时                                ││
│  │  Veggie    ██████████████ 14小时                         ││
│  │  Tree      ████ 4小时                                    ││
│  │  Bedroom   ██ 2小时                                      ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  🚿 热水器数据 (24小时)                                   ││
│  │  ─────────────────────────────────────────────────────  ││
│  │  [折线图: 进水温度 vs 出水温度]                           ││
│  │  [折线图: 水流量]                                         ││
│  │  [时间线: Circulation 状态]                               ││
│  │                                                          ││
│  │  平均出水温度: 121°F  平均进水温度: 103°F                 ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 2.4.2 数据采集规格

**采集机制**: 双重采集策略

| 机制 | 频率/触发 | 采集范围 | 说明 |
|-----|----------|---------|------|
| 定时采集 | 每 30 分钟 | 所有设备 | 基础覆盖 |
| 控制后采集 | 控制操作后 3-10 秒 | 单个设备 | 补充覆盖，记录状态变化 |

**采集内容**:

| 设备 | 字段 | 控制后延迟 |
|-----|------|----------|
| Hue | name, is_on, brightness | 3 秒 |
| Wemo | name, is_on | 3 秒 |
| Rinnai | set_temperature, inlet_temp, outlet_temp, water_flow, is_circulating | 10 秒 |
| Garage | 无（无传感器） | - |

详细设计见 `docs/post_action_collection.md`。

#### 2.4.3 可视化规格

**Hue (Baby Room)**
- 折线图: 亮度 vs 时间 (24小时)
- 统计: 平均亮度、最高亮度、最低亮度

**Wemo (4个开关)**
- 时间线图: ON/OFF 状态变化
- 柱状图: 各开关开启时长统计

**Rinnai 热水器**
- 折线图: 进水温度 vs 出水温度
- 折线图: 水流量变化
- 时间线: Circulation 运行状态
- 统计: 平均温度

---

## 三、技术方案 (RFC)

### 3.1 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React + Vite)                │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Control │  │ Cameras │  │ Schedule│  │ History │        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       │            │            │            │              │
│       └────────────┴────────────┴────────────┘              │
│                    │                                        │
│                    │ HTTP/SSE                               │
└────────────────────┼────────────────────────────────────────┘
                     │
┌────────────────────┼────────────────────────────────────────┐
│                    ▼                                        │
│              FastAPI Backend                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    API Layer                         │   │
│  │  /api/status  /api/cameras  /api/control  /api/...  │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                  │
│  ┌──────────────────────┼──────────────────────────────┐   │
│  │                 Device Layer                         │   │
│  │  ┌──────┐  ┌──────┐  ┌────────┐  ┌────────┐ ┌─────┐│   │
│  │  │ Hue  │  │ Wemo │  │ Rinnai │  │ Meross │ │Cameras│   │
│  │  └──────┘  └──────┘  └────────┘  └────────┘ └─────┘│   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                  │
│  ┌──────────────────────┼──────────────────────────────┐   │
│  │               Scheduler (APScheduler)               │   │
│  │  - Hue 定时任务 (20:00开, 08:20关)                   │   │
│  │  - Wemo 定时任务 (现有)                              │   │
│  │  - 状态采集 (每30分钟)                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                  │
│  ┌──────────────────────┼──────────────────────────────┐   │
│  │                  SQLite                              │   │
│  │  - device_history (设备状态历史)                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 技术选型

| 层级 | 技术 | 理由 |
|-----|------|------|
| 后端框架 | FastAPI | 已有基础，异步支持好 |
| 定时任务 | APScheduler | 已有，轻量级 |
| 数据库 | SQLite | 轻量，单机部署友好 |
| 前端框架 | React 18 | 生态成熟 |
| 构建工具 | Vite | 快速 HMR，开发体验好 |
| UI 框架 | TailwindCSS | 快速开发，响应式 |
| 图表库 | Recharts | React 原生，API 友好 |
| 状态管理 | Zustand | 轻量，够用 |
| HTTP 客户端 | TanStack Query | 缓存、自动刷新 |

### 3.3 开发模式

```bash
# 开发环境
# 后端: FastAPI (端口 8001)
uvicorn main:app --reload --port 8001

# 前端: Vite Dev Server (端口 5173)
# Vite 代理 API 请求到后端
cd frontend && npm run dev
```

### 3.4 生产部署

```bash
# 1. 构建前端
cd frontend && npm run build

# 2. FastAPI serve 静态文件
# main.py 添加:
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")

# 3. 启动服务
uvicorn main:app --port 8001
```

---

## 四、API 设计

### 4.1 端点列表

| 端点 | 方法 | 描述 |
|-----|------|------|
| `/api/status` | GET | 获取所有设备状态 |
| `/api/hue/{light}/toggle` | POST | 切换灯状态 |
| `/api/wemo/{device}/toggle` | POST | 切换开关状态 |
| `/api/rinnai/circulate` | POST | 启动5分钟循环 |
| `/api/garage/{door}/toggle` | POST | 触发车库门 |
| `/api/schedules` | GET | 获取所有定时任务 |
| `/api/history` | GET | 获取历史数据 (支持时间范围) |
| `/api/cameras` | GET | 获取摄像头列表 |
| `/api/cameras/snapshot/{camera_name}` | GET | 获取摄像头快照 (proxy) |

### 4.2 Garage Notification（可选）

车库门 toggle 是敏感动作。后端支持通过 Resend 在每次成功触发后发送邮件通知。该能力默认关闭，只有以下配置全部存在时启用：

```bash
GARAGE_NOTIFY_ENABLED=true
GARAGE_NOTIFY_RECIPIENTS=you@example.com;alerts@example.com
RESEND_API_KEY=your_resend_api_key
RESEND_FROM_EMAIL="Smart Home <notifications@example.com>"
```

`GARAGE_NOTIFY_RECIPIENTS` 支持逗号或分号分隔多个收件人。`RESEND_API_KEY` 可以是已解析的 API key，也可以是 `op://...` 形式的 1Password secret reference；`start_server.sh` 会在启动时解析该 secret reference 后再启动后端。通知失败不会回滚或阻断车库门动作，只会记录错误并在 API 响应的 `notification` 字段中体现。

### 4.3 Cameras API（新增）

**GET /api/cameras**

返回所有摄像头配置列表（不含凭证）。

```json
{
  "cameras": [
    {"name": "Upstairs Patio", "id": "upstairs_patio"},
    {"name": "Frontyard", "id": "frontyard"},
    {"name": "Outer Patio", "id": "outer_patio"},
    {"name": "Backyard", "id": "backyard"},
    {"name": "Heat Pump Side Door", "id": "heat_pump_side_door"},
    {"name": "Downstairs Side Door", "id": "downstairs_side_door"},
    {"name": "Driveway", "id": "driveway"},
    {"name": "Babyroom", "id": "babyroom"}
  ]
}
```

**GET /api/cameras/snapshot/{camera_id}**

异步获取指定摄像头的快照，直接返回 JPEG 图片流。

- **认证**: 后端使用 Digest Auth 向摄像头认证
- **超时**: 15 秒
- **响应**: `image/jpeg`
- **错误**: 504 Gateway Timeout 或 502 Bad Gateway

前端调用方式：
```tsx
// 缩略图（CSS 限制尺寸）
<img src="/api/cameras/snapshot/frontyard" className="w-full h-48 object-cover" />

// 全分辨率（弹窗内）
<img src="/api/cameras/snapshot/frontyard" className="max-w-full max-h-full" />
```

**技术实现要点**：
1. 使用 `httpx.AsyncClient` 并发请求
2. 使用 `httpx.DigestAuth` 处理 Amcrest 的 Digest 认证
3. Streaming Response：后端不缓存图片，直接 pipe 到前端
4. 超时处理：单个摄像头超时不影响其他摄像头

### 4.4 iOS Shortcut API（手机快捷控制）

专为 iOS Shortcuts 设计的简洁 API，支持 GET 请求。

| 端点 | 方法 | 描述 |
|-----|------|------|
| `/api/hue/off` | GET | 关灯（Baby Room） |
| `/api/hue/on` | GET | 开灯，亮度 128（Baby Room） |
| `/api/hue/timer/{minutes}` | GET | 开灯(亮度1) + X分钟后关灯 |
| `/api/hue/timer/{minutes}?brightness=10` | GET | 开灯(指定亮度) + X分钟后关灯 |
| `/api/hue/cancel` | GET | 取消当前 Timer |
| `/api/hue/status` | GET | 获取灯状态 |

**Shortcut 示例配置：**

```
场景1: 关灯
GET http://localhost:8001/api/hue/off

场景2: 开灯（亮度128）
GET http://localhost:8001/api/hue/on

场景3: 开灯（亮度1）+ 7分钟后关灯
GET http://localhost:8001/api/hue/timer/7

场景3变体: 开灯（亮度10）+ 7分钟后关灯
GET http://localhost:8001/api/hue/timer/7?brightness=10

取消 Timer:
GET http://localhost:8001/api/hue/cancel
```

**Timer 行为：**
- 如果已有 Timer 在运行，自动取消旧 Timer，重新开始计时
- 不会叠加多个 Timer

**响应示例：**
```json
{
  "status": "success",
  "light": "Baby room",
  "action": "timer",
  "brightness": 1,
  "minutes": 7,
  "turn_off_at": "2026-02-18T12:07:00",
  "timer_reset": true
}
```

### 4.5 Dashboard API（前端使用）

| 端点 | 方法 | 描述 |
|-----|------|------|
| `/api/status` | GET | 获取所有设备状态 |
| `/api/hue/{light}/toggle` | POST | 切换灯状态 |
| `/api/wemo/{device}/toggle` | POST | 切换开关状态 |
| `/api/rinnai/circulate` | POST | 启动5分钟循环 |
| `/api/garage/{door}/toggle` | POST | 触发车库门 |
| `/api/schedules` | GET | 获取所有定时任务 |
| `/api/history` | GET | 获取历史数据 (支持时间范围) |

### 4.6 响应格式

**GET /api/status**
```json
{
  "hue": {
    "baby_room": { "is_on": true, "brightness": 128 }
  },
  "wemo": {
    "coffee": { "is_on": true },
    "veggie": { "is_on": true },
    "tree": { "is_on": false },
    "bedroom": { "is_on": false }
  },
  "rinnai": {
    "set_temperature": 125,
    "inlet_temp": 103,
    "outlet_temp": 121,
    "is_online": true
  },
  "garage": {
    "door_1": { "available": true },
    "door_2": { "available": true }
  }
}
```

**GET /api/schedules**
```json
{
  "hue": [
    { "time": "20:00", "action": "on", "brightness": 128, "days": "daily" },
    { "time": "08:20", "action": "off", "days": "daily" }
  ],
  "wemo": [
    { "device": "coffee", "time": "07:45", "action": "on", "days": "daily" },
    { "device": "coffee", "time": "11:00", "action": "off", "days": "daily" }
  ],
  "rinnai": [
    { "name": "MorningShower", "start": "07:30", "end": "08:15", "days": "daily" },
    { "name": "AfternoonPeak", "start": "16:30", "end": "18:00", "days": "daily" },
    { "name": "NightShower", "start": "20:30", "end": "23:00", "days": "daily" }
  ]
}
```

**GET /api/history?hours=24**
```json
{
  "hue": [
    { "timestamp": "2026-02-18T10:00:00", "is_on": true, "brightness": 128 },
    { "timestamp": "2026-02-18T10:30:00", "is_on": true, "brightness": 128 }
  ],
  "wemo": {
    "coffee": [
      { "timestamp": "2026-02-18T10:00:00", "is_on": true },
      { "timestamp": "2026-02-18T10:30:00", "is_on": false }
    ]
  },
  "rinnai": [
    { 
      "timestamp": "2026-02-18T10:00:00", 
      "set_temperature": 125, 
      "inlet_temp": 103, 
      "outlet_temp": 121,
      "water_flow": 26,
      "is_circulating": false
    }
  ]
}
```

---

## 五、数据库设计

### 5.1 SQLite Schema

```sql
-- 设备状态历史表
CREATE TABLE device_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_type TEXT NOT NULL,      -- 'hue', 'wemo', 'rinnai'
    device_name TEXT NOT NULL,       -- 'baby_room', 'coffee', etc.
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    data JSON NOT NULL               -- JSON 存储设备特定数据
);

CREATE INDEX idx_device_history_type_name ON device_history(device_type, device_name);
CREATE INDEX idx_device_history_timestamp ON device_history(timestamp);
```

### 5.2 数据存储示例

```sql
-- Hue 记录
INSERT INTO device_history (device_type, device_name, data) 
VALUES ('hue', 'baby_room', '{"is_on": true, "brightness": 128}');

-- Wemo 记录
INSERT INTO device_history (device_type, device_name, data) 
VALUES ('wemo', 'coffee', '{"is_on": true}');

-- Rinnai 记录
INSERT INTO device_history (device_type, device_name, data) 
VALUES ('rinnai', 'main_house', '{"set_temperature": 125, "inlet_temp": 103, "outlet_temp": 121, "water_flow": 26, "is_circulating": false}');
```

---

## 六、文件结构

```
smart_home/
├── main.py                     # FastAPI 主程序 (更新)
├── requirements.txt            # Python 依赖 (更新)
├── config/
│   ├── wemo_config.example.yaml  # Wemo 配置模板
│   ├── wemo_config.yaml          # 实际配置（gitignore，从 example 复制）
│   └── cameras.yaml              # 摄像头配置 (新增)
├── .env                        # 环境变量
│
├── api/                        # API 路由 (更新)
│   ├── __init__.py
│   ├── status.py               # 状态查询
│   ├── control.py              # 设备控制
│   ├── schedule.py             # 定时任务
│   ├── history.py              # 历史数据
│   └── cameras.py              # 摄像头 API (新增)
│
├── models/                     # 数据模型
│   ├── __init__.py
│   ├── device.py               # 设备模型
│   └── history.py              # 历史记录模型
│
├── services/                   # 业务逻辑 (更新)
│   ├── __init__.py
│   ├── hue_service.py          # Hue 服务
│   ├── wemo_service.py         # Wemo 服务
│   ├── rinnai_service.py       # Rinnai 服务
│   ├── meross_service.py       # Meross 服务
│   ├── notification_service.py # Resend 通知服务
│   ├── camera_service.py       # 摄像头服务 (新增)
│   ├── scheduler.py            # 定时任务管理
│   └── wemo_schedule.py        # Wemo 定时任务 (现有)
│
├── ref_cameras/                # 参考实现 (不参与构建)
│   ├── Config.py
│   ├── IntervalRecorder.py
│   └── main3_nood.py
│
├── data/                       # 数据存储
│   └── smart_home.db           # SQLite 数据库
│
├── frontend/                   # React 前端 (更新)
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── components/
│       │   ├── Layout.tsx
│       │   ├── ControlTab.tsx
│       │   ├── CamerasTab.tsx       # 新增
│       │   ├── CameraCard.tsx       # 新增
│       │   ├── CameraModal.tsx      # 新增
│       │   ├── ScheduleTab.tsx
│       │   ├── HistoryTab.tsx
│       │   ├── HueCard.tsx
│       │   ├── WemoCard.tsx
│       │   ├── RinnaiCard.tsx
│       │   ├── GarageCard.tsx
│       │   └── charts/
│       │       ├── BrightnessChart.tsx
│       │       ├── SwitchTimeline.tsx
│       │       └── HeaterChart.tsx
│       ├── hooks/
│       │   ├── useStatus.ts
│       │   ├── useCameras.ts        # 新增
│       │   ├── useSchedules.ts
│       │   └── useHistory.ts
│       └── stores/
│           └── deviceStore.ts
│
└── docs/
    └── dev_dashboard.md        # 本文档
```

---

## 七、实施计划

### Phase 1: 后端重构 (1-2 天)

1. 创建 `api/` 目录，拆分路由
2. 创建 `services/` 目录，封装设备操作
3. 实现 SQLite 数据存储
4. 添加状态采集定时任务 (每30分钟)
5. 添加 Hue 定时任务 (20:00开, 08:20关)

### Phase 2: 摄像头集成 (1 天)

1. 创建 `api/cameras.py` - 摄像头 API 路由
2. 创建 `services/camera_service.py` - 摄像头服务
3. 创建 `config/cameras.yaml` - 摄像头配置
4. 实现异步 proxy：从 Amcrest 获取快照并直接返回
5. 测试 Digest Auth 认证

### Phase 3: 前端开发 (2-3 天)

1. 初始化 React + Vite 项目
2. 实现 Control Tab (设备控制)
3. 实现 Cameras Tab (监控预览)
   - CamerasTab.tsx: 主容器，管理所有摄像头状态
   - CameraCard.tsx: 单个摄像头卡片，显示缩略图
   - CameraModal.tsx: 全分辨率弹窗
   - useCameras.ts: 管理摄像头加载状态
4. 实现 Schedule Tab (定时任务展示)
5. 实现 History Tab (历史数据可视化)

### Phase 4: 集成测试 (1 天)

1. 端到端测试
2. 生产构建测试
3. 部署验证

---

## 八、注意事项

### 8.1 Meross 车库门

- 传感器未安装，无法获取真实状态
- 仅提供触发功能，不显示开/关状态
- Garage Door 3 未接线，前端仅显示 Door 1 和 2
- 触发动作通过 POST API 执行；若配置了 Resend 通知，每次触发后发送邮件

### 8.2 时区

- 所有定时任务使用 Pacific Time (PT)
- APScheduler 配置时区: `America/Los_Angeles`

### 8.3 Rinnai Schedule

- Schedule 存储在 Rinnai 云端，仅读取展示
- 不在后端创建/修改 schedule

### 8.4 数据保留

- SQLite 历史数据暂不清理
- 后续可添加定期清理策略 (如保留 30 天)

### 8.5 Amcrest 摄像头

- **认证方式**: Digest Auth（非 Basic Auth）
- **快照接口**: `http://{IP}/cgi-bin/snapshot.cgi`
- **超时设置**: 15 秒（网络不稳定时可能需要调整）
- **无状态存储**: 不记录摄像头历史，不做周期性抓取
- **参考实现**: `ref_cameras/IntervalRecorder.py` 提供了完整的 Amcrest 抓取实现
- **并发控制**: 前端应控制并发请求数，避免同时请求过多摄像头导致浏览器连接数限制
