# Hue Light Control Server

一个基于FastAPI的Philips Hue灯控制服务器，提供RESTful API来控制Hue灯的开关和定时功能。

## 功能特点

- 通过HTTP API控制Hue灯
- 支持即时开关和延时关闭功能
- 自动保存和恢复灯的状态
- 完整的错误处理和日志记录
- 支持环境变量配置
- 包含单元测试和集成测试

## 快速开始

### 前提条件

- Python 3.10 或更高版本
- Philips Hue Bridge 和灯泡
- Bridge 的 IP 地址
- 灯泡的名称

### 安装

1. 克隆仓库：
```bash
git clone https://github.com/grapeot/hue_server.git
cd hue_server
```

2. 创建并激活虚拟环境：
```bash
python -m venv py310
source py310/bin/activate  # Linux/Mac
# 或
.\py310\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
```bash
cp .env.example .env
```
编辑 `.env` 文件，设置：
- `HUE_BRIDGE_IP`：Hue Bridge 的 IP 地址
- `HUE_LIGHT_NAME`：要控制的灯的名称
- `PORT`：服务器端口（默认8000）

### 首次使用

1. 找到您的 Hue Bridge IP 地址：
   - 在 Hue App 中查看
   - 或访问 https://discovery.meethue.com/

2. 首次运行时需要与 Bridge 配对：
   - 启动服务器
   - 在看到提示后，按下 Bridge 上的物理按钮

### 运行服务器

```bash
python main.py
```
或使用 uvicorn：
```bash
uvicorn main:app --reload
```

## API 使用说明

### 1. 打开灯并设置延时关闭
```
GET /light/{minutes}
```
- `minutes`：延时关闭时间（分钟），可以使用小数
- 示例：`GET /light/5` 打开灯并在5分钟后关闭
- 特殊情况：`GET /light/0` 立即关闭灯

### 2. 查询灯的状态
```
GET /status
```
返回灯的当前状态，包括开关状态和亮度。

### 3. 设置灯的状态
```
POST /state
Content-Type: application/json

{
    "on": true,
    "bri": 254
}
```
- `on`：开关状态（true/false）
- `bri`：亮度（0-254）

## 项目结构

```
hue_server/
├── main.py              # 主应用文件，包含FastAPI应用和路由
├── test_unit.py         # 单元测试
├── test_integration.py  # 集成测试
├── requirements.txt     # 项目依赖
├── .env.example        # 环境变量模板
└── README.md           # 项目文档
```

### 主要组件

- `main.py`
  - FastAPI 应用程序
  - Hue Bridge 连接管理
  - API 路由和处理函数
  - 错误处理和日志记录

- `test_unit.py`
  - 单元测试套件
  - Mock 对象和测试用例
  - 测试各种边界情况

- `test_integration.py`
  - 集成测试
  - 实际设备交互测试
  - 状态保存和恢复测试

## 开发指南

### 环境设置

1. 创建开发分支：
```bash
git checkout -b feature/your-feature
```

2. 安装开发依赖：
```bash
pip install -r requirements.txt
```

### 运行测试

1. 单元测试：
```bash
python -m unittest test_unit.py -v
```

2. 集成测试（需要实际的 Hue 设备）：
```bash
python test_integration.py
```

### 代码风格

- 使用 Python 类型注解
- 保持函数简洁，单一职责
- 添加适当的注释和文档字符串
- 使用有意义的变量和函数名

### 提交代码

1. 确保测试通过：
```bash
python -m unittest discover -v
```

2. 提交更改：
```bash
git add .
git commit -m "[Cursor] 你的提交信息"
```

3. 创建 Pull Request：
```bash
gh pr create --title "[Cursor] 你的PR标题" --body-file pr_description.md
```

## 故障排除

### 常见问题

1. Bridge 连接失败
   - 确认 IP 地址正确
   - 检查网络连接
   - 确认已按下配对按钮

2. 找不到灯
   - 检查灯的名称是否正确
   - 确认灯在 Hue App 中可见
   - 检查灯是否已连接到 Bridge

3. 状态更新延迟
   - 检查网络延迟
   - 确认 Bridge 响应正常

### 调试

- 检查日志输出
- 使用 `/status` 端点验证状态
- 确认环境变量设置正确

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

请确保：
- 添加测试用例
- 更新文档
- 遵循代码风格
- 提供清晰的提交信息

## 许可证

MIT License 