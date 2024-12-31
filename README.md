# Hue Light Control Server

这是一个使用FastAPI实现的Philips Hue灯控制服务器。它提供了一个简单的API来控制Hue灯，可以打开灯并在指定时间后自动关闭。

## 功能

- 通过GET请求打开灯并设置自动关闭时间
- 查询灯的当前状态
- 自动关闭功能

## 安装

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
   - 复制 `.env.example` 为 `.env`
   - 填写您的Hue Bridge IP地址和灯的名称

## 首次设置

1. 找到您的Hue Bridge IP地址：
   - 可以在Hue App中查看
   - 或者访问 https://discovery.meethue.com/

2. 在首次运行服务器之前，确保：
   - 已正确设置 `.env` 文件
   - 准备好按下Hue Bridge上的物理按钮（首次连接需要）

## 运行服务器

```bash
uvicorn main:app --reload
```

## API 使用说明

1. 打开灯并设置自动关闭时间：
```
GET /light/{minutes}
```
例如：`GET /light/5` 将打开灯并在5分钟后自动关闭

2. 查询灯的状态：
```
GET /status
```

## 调试

服务器运行时会输出详细的日志信息，可以帮助诊断问题。 