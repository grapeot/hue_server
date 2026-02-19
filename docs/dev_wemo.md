# Wemo设备控制功能文档

## 概述

本项目已扩展支持Wemo智能设备的控制功能。由于Belkin在2026年1月31日后停止对Wemo的维护，本服务器提供了本地网络控制Wemo设备的能力，包括设备发现、开关控制和定时任务管理。

## 功能特性

1. **设备管理**：支持hardcode设备信息或按需发现更新
2. **设备控制**：通过RESTful API控制Wemo设备的开关
3. **定时任务**：支持基于Pacific时间的定时任务配置
4. **集中配置**：通过YAML配置文件统一管理设备信息和定时任务

## 安装和配置

### 依赖安装

确保已安装所有必需的Python包：

```bash
pip install -r requirements.txt
```

主要新增依赖：
- `pywemo==1.3.1`：Wemo设备控制库
- `pytz==2024.1`：时区支持
- `pyyaml==6.0.1`：YAML配置文件解析
- `APScheduler==3.10.4`：定时任务调度库

### 环境变量配置

在`.env`文件中可以配置以下选项（可选）：

```bash
# Wemo配置文件路径（默认：config/wemo_config.yaml）
WEMO_CONFIG_FILE=config/wemo_config.yaml

# 是否在启动时自动发现设备（默认：false，使用hardcode配置）
WEMO_AUTO_DISCOVER=false
```

### 配置文件示例

创建`config/wemo_config.yaml`文件：

```yaml
# Wemo设备配置
# 设备信息hardcode，因为设备固定不变，无需频繁发现
devices:
  - name: "Coffee"
    host: "192.168.180.135"
    port: 49153
    type: "Switch"
    description: "咖啡机开关"  # 可选：设备描述
  
  - name: "Bedroom Light"
    host: "192.168.180.57"
    port: 49153
    type: "LightSwitchLongPress"
    description: "卧室灯光"
  
  - name: "Tree"
    host: "192.168.180.175"
    port: 49153
    type: "Insight"
    description: "圣诞树灯光"
  
  - name: "Veggie"
    host: "192.168.180.68"
    port: 49153
    type: "Insight"
    description: "蔬菜灯"

# 定时任务配置
schedule:
  # 全局时区设置（Pacific, UTC, 或 local）
  timezone: "Pacific"
  
  # 定时任务列表
  tasks:
    # Pacific时间每天早上7:45开启coffee switch
    - time: "07:45"
      device: "Coffee"  # 必须与devices中的name字段完全匹配（不区分大小写）
      action: "on"
      description: "早上开启咖啡机"  # 可选：任务描述
    
    # Pacific时间每天中午11:00关闭coffee switch
    - time: "11:00"
      device: "Coffee"
      action: "off"
      description: "中午关闭咖啡机"
    
    # 示例：使用秒级精度（可选）
    # - time: "22:30:00"
    #   device: "Bedroom Light"
    #   action: "off"
    #   description: "晚上关闭卧室灯"
```

**配置说明**：
- `devices`：设备列表，每个设备包含名称、IP、端口、类型等信息
- `description`：可选，设备或任务的描述信息
- `schedule.tasks`：定时任务列表，每个任务指定时间、设备和动作
- **设备名称匹配**：API调用时使用精确匹配（case-insensitive），设备名称必须与配置中的`name`字段完全一致

## 脚本工具

### refresh_wemo_devices.py - 刷新设备配置

位于`scripts/refresh_wemo_devices.py`，用于重新发现设备并更新`config/wemo_config.yaml`：

```bash
python scripts/refresh_wemo_devices.py
```

该脚本会：
1. 扫描局域网发现所有Wemo设备
2. 读取现有的`config/wemo_config.yaml`（如果存在）
3. 更新设备信息（IP、端口、类型等）
4. 保留现有的定时任务配置
5. 保存更新后的配置文件

**使用场景**：当设备IP地址发生变化时（如路由器重启），运行此脚本更新配置。

## API端点

### 1. 列出所有Wemo设备

```
GET /wemo/devices
```

返回所有发现的Wemo设备列表，包括设备名称、IP地址、端口、类型和当前状态。

**响应示例**：
```json
{
  "status": "success",
  "count": 2,
  "devices": [
    {
      "name": "Coffee Maker",
      "host": "192.168.1.100",
      "port": 49153,
      "type": "Switch",
      "state": "off"
    },
    {
      "name": "Bedroom Light",
      "host": "192.168.1.101",
      "port": 49154,
      "type": "LightSwitch",
      "state": "on"
    }
  ]
}
```

### 2. 开启Wemo设备

```
POST /wemo/{device_name}/on
```

开启指定名称的Wemo设备。设备名称必须与配置文件中的`name`字段完全匹配（不区分大小写）。

**示例**：
```bash
curl -X POST http://localhost:8000/wemo/coffee/on
```

**响应示例**：
```json
{
  "status": "success",
  "message": "Device coffee turned on",
  "device_name": "Coffee Maker",
  "state": "on",
  "timestamp": "2026-01-31T12:00:00"
}
```

### 3. 关闭Wemo设备

```
POST /wemo/{device_name}/off
```

关闭指定名称的Wemo设备。

**示例**：
```bash
curl -X POST http://localhost:8000/wemo/coffee/off
```

### 4. 获取设备状态

```
GET /wemo/{device_name}/status
```

获取指定Wemo设备的当前状态。

**响应示例**：
```json
{
  "name": "Coffee Maker",
  "host": "192.168.1.100",
  "port": 49153,
  "type": "Switch",
  "state": "on",
  "timestamp": "2026-01-31T12:00:00"
}
```

### 5. 查看定时任务

```
GET /wemo/schedule/tasks
```

查看所有已配置的定时任务。

**响应示例**：
```json
{
  "status": "success",
  "count": 2,
  "tasks": [
    {
      "time": "07:45:00",
      "device": "Coffee",
      "action": "on",
      "timezone": "Pacific"
    },
    {
      "time": "11:00:00",
      "device": "Coffee",
      "action": "off",
      "timezone": "Pacific"
    }
  ],
  "config_file": "config/wemo_config.yaml"
}
```


## 配置设计

### 配置文件格式

所有Wemo相关配置统一使用YAML格式，默认路径为`config/wemo_config.yaml`。

**配置文件结构**：
```yaml
# Wemo设备配置
devices:
  # 方式1: Hardcode设备信息（推荐，因为设备固定不变）
  - name: "Coffee"
    host: "192.168.180.135"
    port: 49153
    type: "Switch"
    alias: ["coffee", "coffee maker"]  # 可选：设备别名，用于API调用时的匹配
  
  - name: "Bedroom Light"
    host: "192.168.180.57"
    port: 49153
    type: "LightSwitchLongPress"
    alias: ["bedroom", "bedroom light"]
  
  - name: "Tree"
    host: "192.168.180.175"
    port: 49153
    type: "Insight"
  
  - name: "Veggie"
    host: "192.168.180.68"
    port: 49153
    type: "Insight"

# 定时任务配置
schedule:
  timezone: "Pacific"  # 默认时区：Pacific, UTC, 或 local
  
  tasks:
    # Pacific时间每天早上7:45开启coffee switch
    - time: "07:45"
      device: "Coffee"  # 使用设备名称或别名
      action: "on"
    
    # Pacific时间每天中午11:00关闭coffee switch
    - time: "11:00"
      device: "Coffee"
      action: "off"
    
    # 也可以使用秒级精度
    - time: "08:30:00"
      device: "Bedroom Light"
      action: "on"
```

### 设备配置说明

#### Hardcode模式（推荐）

由于Wemo设备已经固定且不再新增，推荐使用hardcode模式：
- **优点**：
  - 启动速度快，无需等待设备发现
  - 不依赖网络发现，更稳定可靠
  - 可以预先配置设备别名，API调用更灵活
  - 避免每次启动都进行网络扫描
  
- **配置方式**：在`devices`列表中直接指定设备的`name`、`host`、`port`和`type`
- **设备信息获取**：首次配置时，可以使用`test_wemo.py`脚本或`GET /wemo/devices` API获取设备信息

#### 按需发现模式

如果需要更新设备信息，可以通过API触发：
- **API端点**：`POST /wemo/discover` - 重新发现所有设备并更新配置
- **使用场景**：
  - 设备IP地址发生变化（如路由器重启后重新分配IP）
  - 添加了新设备（虽然不太可能）
  - 验证hardcode配置是否正确

### 定时任务配置说明

- **time**：时间格式为`HH:MM`或`HH:MM:SS`（24小时制）
- **device**：设备名称或别名（不区分大小写，支持部分匹配）
- **action**：`on`（开启）或`off`（关闭）
- **timezone**：全局时区设置，可在单个任务中覆盖（未来功能）

### 配置文件位置

- 默认位置：`config/wemo_config.yaml`
- 可通过环境变量`WEMO_CONFIG_FILE`自定义路径

### 时区说明

- **Pacific时间**：使用`America/Los_Angeles`时区，自动处理夏令时（DST）
- **UTC时间**：协调世界时
- **本地时间**：服务器所在时区的本地时间

### 定时任务执行

- 定时任务在服务器启动时从YAML配置文件加载
- 使用APScheduler（Advanced Python Scheduler）进行任务调度
- 支持cron风格的定时表达式，基于配置的时区执行（默认Pacific时间）
- 任务执行日志会记录在服务器日志中
- 修改配置文件后需要重启服务器才能生效（未来可能支持热重载）

**APScheduler优势**：
- 标准库，广泛使用，成熟可靠
- 支持cron语法，配置清晰
- 内置时区支持，自动处理夏令时
- 与FastAPI集成简单（BackgroundScheduler）
- 资源消耗低，无需持续轮询

## 设备管理机制

### 启动时设备加载

服务器启动时的行为取决于配置：

1. **Hardcode模式（默认，推荐）**：
   - 从`config/wemo_config.yaml`读取hardcode的设备信息
   - 直接使用配置中的IP地址和端口连接设备
   - 不进行网络扫描，启动速度快
   - 如果设备连接失败，会在日志中记录警告，但不影响服务器启动

2. **自动发现模式**（`WEMO_AUTO_DISCOVER=true`）：
   - 启动时扫描局域网发现设备
   - 发现的设备信息会与配置文件中的hardcode信息合并
   - 如果发现新设备或IP变化，会记录到日志中

### 设备匹配机制

API调用时使用精确匹配：
- 设备名称必须与配置文件中的`name`字段完全一致（不区分大小写）
- 例如：配置中设备名为`"Bedroom Light"`，API调用可以使用`/wemo/bedroom light/on`或`/wemo/Bedroom Light/on`
- 不支持部分匹配或别名

### 按需更新设备信息

当设备信息需要更新时（如IP地址变化）：
1. 运行`scripts/refresh_wemo_devices.py`脚本重新发现设备
2. 脚本会自动更新`config/wemo_config.yaml`中的设备信息（IP、端口、类型）
3. 保留现有的定时任务配置
4. 重启服务器应用新配置

## 故障排除

### 设备未发现

1. **检查网络连接**：确保服务器和Wemo设备在同一局域网内
2. **检查防火墙**：确保UPnP端口（通常是49152-49154）未被阻止
3. **手动指定IP**：如果自动发现失败，可以在代码中手动指定设备IP地址

### 设备控制失败

1. **检查设备名称**：使用`GET /wemo/devices`确认准确的设备名称
2. **检查设备在线状态**：确保Wemo设备已连接电源和WiFi
3. **查看日志**：检查服务器日志获取详细错误信息

### 定时任务不执行

1. **检查配置文件**：确认`config/wemo_config.yaml`格式正确，YAML语法无误
2. **检查设备名称**：确认定时任务中的设备名称与配置文件中的设备名称匹配
3. **检查时区**：确认配置文件中的时区设置正确
4. **查看日志**：检查定时任务调度器的启动日志，确认任务已加载

## 技术实现

### 设备控制

使用`pywemo`库进行设备控制：
- 基于Wemo的UPnP/SOAP协议
- 支持本地网络控制，无需云服务
- 兼容各种Wemo设备类型（Switch、LightSwitch、Insight等）

### 定时任务

**实现方式**：APScheduler（Advanced Python Scheduler）
- 使用`BackgroundScheduler`在后台运行
- 使用`CronTrigger`支持cron风格的定时表达式
- 内置时区支持，自动处理夏令时（DST）
- 任务调度由APScheduler内部管理，无需轮询

**APScheduler特点**：
- **标准库**：广泛使用的Python定时任务库，成熟可靠
- **Cron语法**：支持标准的cron表达式，配置清晰易读
- **时区支持**：内置时区处理，自动处理夏令时转换
- **资源高效**：无需持续轮询，只在任务时间触发
- **集成简单**：与FastAPI无缝集成，使用BackgroundScheduler

**执行流程**：
1. 服务器启动时从YAML配置文件加载定时任务
2. 为每个任务创建APScheduler的CronTrigger
3. 使用BackgroundScheduler在后台运行
4. APScheduler在指定时间自动触发任务执行
5. 任务执行日志记录在服务器日志中

**示例配置映射**：
```yaml
# YAML配置
- time: "07:45"
  device: "Coffee"
  action: "on"
```
映射到APScheduler：
```python
scheduler.add_job(
    func=execute_task,
    trigger=CronTrigger(hour=7, minute=45, timezone='America/Los_Angeles'),
    id='coffee_on_0745'
)
```

### 架构设计

- Wemo功能与现有Hue功能并行运行
- 共享FastAPI应用实例
- 独立的设备管理器和调度器
- 设备信息优先使用hardcode配置，通过脚本按需更新
- 统一使用YAML配置文件管理设备和定时任务
- API只提供查询和控制功能，不提供配置修改功能（配置通过YAML文件管理）
- 使用APScheduler进行定时任务调度，标准且可靠

### 配置管理流程

1. **初始配置**：
   - 运行`scripts/refresh_wemo_devices.py`发现设备并生成初始配置文件
   - 或调用`GET /wemo/devices`获取设备信息后手动创建`config/wemo_config.yaml`
   - 在配置文件中hardcode设备信息并配置定时任务

2. **日常运行**：
   - 服务器启动时从YAML文件加载hardcode配置
   - 直接连接设备，无需网络扫描
   - 定时任务自动执行

3. **设备信息更新**（如IP变化）：
   - 运行`scripts/refresh_wemo_devices.py`脚本
   - 脚本自动更新`config/wemo_config.yaml`中的设备信息
   - 重启服务器应用新配置

## 设计优势

### Hardcode配置的优势

1. **性能优化**：
   - 启动速度快，无需等待网络扫描
   - 减少网络请求，降低网络负载
   - 避免UPnP发现的不稳定性

2. **可靠性提升**：
   - 不依赖网络发现，即使网络有问题也能连接已知设备
   - 设备信息固定，避免IP变化导致的连接失败
   - 可以预先验证配置的正确性

3. **简洁性**：
   - 精确匹配，避免歧义
   - 配置集中管理，易于维护
   - API设计简洁，职责清晰

4. **适用场景**：
   - 设备固定不变（符合当前使用场景）
   - 不需要频繁添加新设备
   - 追求稳定性和性能

### YAML配置的优势

相比纯文本配置：
- **结构化**：清晰的层次结构，易于理解
- **类型安全**：支持数据类型，减少配置错误
- **可扩展**：易于添加新配置项（如别名、描述等）
- **可读性**：支持注释，配置更清晰
- **工具支持**：有丰富的YAML解析和验证工具

相比JSON配置：
- **可读性更好**：不需要引号，格式更简洁
- **支持注释**：可以在配置文件中添加说明
- **更人性化**：更适合手工编辑

## 未来改进

- [ ] 支持配置文件热重载（无需重启服务器，重新加载APScheduler任务）
- [ ] 支持更复杂的定时规则（如工作日/周末、特定日期）- APScheduler的CronTrigger已支持
- [ ] 支持设备分组和场景控制
- [ ] 添加设备状态变化通知/Webhook
- [ ] 自动检测设备IP变化并更新配置（可选）
- [ ] 添加设备能耗监控和历史记录（适用于Insight设备）
- [ ] 配置文件验证和错误提示
- [ ] 支持配置模板和预设
- [ ] 添加任务执行历史记录和统计

## 相关资源

- [pywemo项目主页](https://github.com/pywemo/pywemo)
- [Wemo设备文档](https://www.belkin.com/us/support-article?articleNum=11227)
