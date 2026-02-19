# Rinnai Control-R 热水器 API 控制

## 设备信息

| 项目 | 值 |
|------|-----|
| IP | 192.168.180.177 |
| MAC | 24:58:7c:25:2c:14 (Espressif) |
| Device ID | TF.XE-007042 |
| Thing Name | CR_3661475f-4ab1-7025-625e-78c38235726e |
| 固件 | 1.0.1 |

## 环境配置

```bash
# 安装依赖
source /Users/grapeot/co/knowledge_working/.venv/bin/activate
uv pip install aiorinnai python-dotenv

# .env 文件
USERNAME=your_email@example.com
PASSWORD=your_password
```

## 连接方式

### 本地直连（不可用）

固件 1.0.1 **不支持** 本地直连。端口 9798/9799 未开放。

### 云端 API（可用）

通过 AWS Cognito 认证 + GraphQL API 控制。

```python
from aiorinnai import API

async with API() as api:
    await api.async_login(username, password)
    # 使用 api.device 操作设备
```

## 常见操作

### 1. 获取设备状态

```python
user_info = await api.user.get_info()
devices = user_info.get("devices", {}).get("items", [])
device = devices[0]

# 获取详细状态
info = await api.device.get_info(device["id"])
data = info["data"]["getDevice"]

# 传感器数据
sensor_data = data["info"]
# m02_outlet_temperature: 出水温度
# m08_inlet_temperature: 进水温度  
# m01_water_flow_rate_raw: 水流量
# m04_combustion_cycles: 燃烧循环次数

# Shadow 状态
shadow = data["shadow"]
# operation_enabled: 是否启用
# recirculation_enabled: 循环是否启用
# set_domestic_temperature: 设定温度
```

### 2. 温度控制

```python
# 设置温度 (华氏度，范围 110-140)
await api.device.set_temperature(device, 125)

# 开关设备
await api.device.turn_on(device)
await api.device.turn_off(device)
```

### 3. 循环控制

```python
# 启动循环 (1-60 分钟，但超过 5 分钟可能有 bug)
await api.device.start_recirculation(device, 5)

# 停止循环
await api.device.stop_recirculation(device)
```

### 4. 假期模式

```python
await api.device.enable_vacation_mode(device)
await api.device.disable_vacation_mode(device)
```

### 5. 创建 Schedule（需直接调用 GraphQL）

aiorinnai 库不支持，需直接调用：

```python
import uuid
from aiorinnai.const import GRAPHQL_ENDPOINT, GET_PAYLOAD_HEADERS

CREATE_SCHEDULE_MUTATION = """
mutation CreateDeviceSchedule($input: CreateDeviceScheduleInput!, $condition: ModelDeviceScheduleConditionInput) {
  createDeviceSchedule(input: $input, condition: $condition) {
    id
    serial_id
    name
    days
    times
    schedule_date
    active
  }
}
"""

variables = {
    "input": {
        "id": str(uuid.uuid4()).upper(),
        "serial_id": "TF.XE-007042",  # 设备 ID
        "name": "ScheduleName",
        "days": ["{0=Su,1=M,2=T,3=W,4=Th,5=F,6=S}"],  # 每天
        "times": ["{start=16:30,end=18:00}"],
        "schedule_date": "02/17/2026 20:50",  # 当前日期时间
        "active": True,
    }
}

headers = {**GET_PAYLOAD_HEADERS, "Authorization": api.id_token}
payload = json.dumps({"query": CREATE_SCHEDULE_MUTATION, "variables": variables})

async with api._get_session().post(GRAPHQL_ENDPOINT, data=payload, headers=headers) as resp:
    result = await resp.json()
```

**Days 格式：**
- 每天: `{0=Su,1=M,2=T,3=W,4=Th,5=F,6=S}`
- 工作日: `{1=M,2=T,3=W,4=Th,5=F}`
- 周末: `{0=Su,6=S}`

**更新 Schedule：**
```python
UPDATE_SCHEDULE_MUTATION = """
mutation UpdateDeviceSchedule($input: UpdateDeviceScheduleInput!, $condition: ModelDeviceScheduleConditionInput) {
  updateDeviceSchedule(input: $input, condition: $condition) {
    id name days times active
  }
}
"""
# variables["input"]["id"] = existing_schedule_id
```

**删除 Schedule：**
```python
DELETE_SCHEDULE_MUTATION = """
mutation DeleteDeviceSchedule($input: DeleteDeviceScheduleInput!, $condition: ModelDeviceScheduleConditionInput) {
  deleteDeviceSchedule(input: $input, condition: $condition) {
    id
  }
}
"""
```

## API 端点

| 端点 | 用途 |
|------|------|
| `https://s34ox7kri5dsvdr43bfgp6qh6i.appsync-api.us-east-1.amazonaws.com/graphql` | GraphQL API |
| `https://d1coipyopavzuf.cloudfront.net/api/device_shadow/input` | Shadow 命令 |

## 注意事项

1. **循环时间 bug**：Rinnai API 循环超过 5 分钟可能无法正常工作，建议用 schedule 替代
2. **无本地 API**：固件 1.0.1 不开放本地端口，只能走云端
3. **安全性**：API 读取数据无鉴权，任何人知道设备 ID 可读取
4. **Connected 状态**：`api.is_connected` 可能显示 False，但实际可用
5. **schedule_date**：创建 schedule 时需提供当前日期时间

## 相关资源

- aiorinnai 库: https://github.com/explosivo22/aiorinnai
- Home Assistant 集成: https://github.com/explosivo22/rinnaicontrolr-ha
- 官方 App: Rinnai Central (需 2.0 版本)

## 示例脚本

- `test_api.py` - 读取设备状态
- `scripts/create_schedule.py` - 创建 schedule
- `scripts/introspect_schema.py` - 查询 GraphQL schema
