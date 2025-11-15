# OpenContext Capture Control

OpenContext支持两种运行模式：普通模式（包含录屏）和无录屏模式。

## 运行模式

### 1. 普通模式（默认启动录屏）
```bash
uv run opencontext start --config config/config.yaml
```

此模式会启动所有capture组件，包括：
- 截图录制（每5秒截取一次屏幕）
- 文件监控（如果启用）
- Vault文档监控（如果启用）

### 2. 无录屏模式（禁用capture）
```bash
uv run opencontext start --config config/config.yaml --no-capture
```

此模式启动后端服务但**不会**启动任何capture组件，适合以下场景：
- 作为glass模块的后端服务
- 只需要API查询功能
- 不需要实时上下文捕获

## 使用场景

### Glass模块集成
当将OpenContext作为glass模块的后端服务时，推荐使用`--no-capture`模式：

```bash
# 启动无录屏的后端服务
uv run opencontext start --port 8000 --no-capture

# 在另一个终端处理glass视频
uv run glass start 15-11 --config config/config.yaml
```

### 独立上下文捕获
当需要OpenContext进行实时上下文捕获时，使用普通模式：

```bash
# 启动包含录屏的服务
uv run opencontext start --port 8000
```

## 配置说明

- `--no-capture`是命令行选项，会覆盖配置文件中的capture设置
- 该选项支持多进程模式（`--workers`参数）
- 可以与其它启动参数组合使用

## 完整参数列表

```bash
uv run opencontext start [选项]

选项：
  --config CONFIG          配置文件路径
  --host HOST              绑定地址（覆盖配置文件）
  --port PORT              绑定端口（覆盖配置文件）
  --workers WORKERS        工作进程数（默认：1）
  --no-capture            禁用上下文捕获（不启动截图/文件监控）
  --help                  显示帮助信息
```