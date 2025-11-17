# MineContext Glass Electron开发指南

## 🎯 项目概述

MineContext Glass 是一个基于 Electron + Python 的混合架构桌面应用，提供真正的GUI用户体验。

### 🏗️ 技术架构

```
MineContext Glass.app
├── Electron 主进程 (JavaScript)
│   ├── 窗口管理
│   ├── Python 子进程管理
│   └── IPC 通信
├── Python 后端 (FastAPI)
│   ├── REST API 服务
│   ├── 视频处理
│   └── AI 分析
└── React 前端 (WebUI)
    ├── 用户界面
    ├── 状态管理
    └── API 调用
```

## 📁 项目结构

```
MineContext-Glass/
├── electron/                 # Electron 主进程
│   ├── main.js             # 主进程入口
│   └── preload.js          # 预加载脚本
├── backend/                # Python 后端服务
│   └── main.py            # 后端服务入口
├── webui/                  # React 前端
│   ├── src/
│   └── dist/              # 构建产物
├── scripts/               # 构建脚本
│   └── build-electron.js
├── assets/                # 应用资源
└── package.json           # 项目配置
```

## 🚀 快速开始

### 环境要求

- **Node.js**: v18+
- **Python**: 3.9+
- **uv**: Python 包管理器
- **macOS**: 11.0+ (Intel + Apple Silicon)

### 安装依赖

```bash
# 安装 Electron 依赖
npm install

# 安装 Python 依赖
uv sync
```

### 开发模式

```bash
# 启动 Electron 应用（开发模式）
npm run electron-dev
```

这将同时启动：
- React 前端开发服务器 (http://localhost:5174)
- Python 后端服务 (动态端口)
- Electron 主进程

### 构建应用

```bash
# 构建完整应用
npm run build
```

构建流程：
1. 构建前端资源 (`npm run build-frontend`)
2. 构建 Python 后端 (`npm run build-backend`)
3. 构建 Electron 应用 (`npm run build-electron`)

## 🛠️ 开发指南

### 前端开发

前端位于 `webui/` 目录，使用 React + TypeScript + Vite：

```bash
cd webui
npm run dev     # 开发服务器
npm run build   # 生产构建
```

### 后端开发

Python 后端位于项目根目录，使用 FastAPI：

```bash
uv run opencontext start --port 8001 --no-capture
```

### Electron 开发

Electron 主进程位于 `electron/` 目录：

```bash
npm run electron     # 运行 Electron 应用
npm run electron-dev # 开发模式（同时启动前后端）
```

## 🔧 配置说明

### package.json

主要配置项：
- `main`: Electron 主进程入口
- `scripts.build`: 构建命令
- `build`: electron-builder 构建配置

### 环境检测

应用会自动检测运行环境：
- **开发环境**: 连接 Vite 开发服务器
- **生产环境**: 使用构建的静态文件
- **Electron 环境**: 动态 API 端口配置

### 进程间通信

通过 `preload.js` 提供安全的 API 桥接：

```javascript
// 在渲染进程中
window.electronAPI.getBackendPort()
window.electronAPI.restartBackend()
window.electronAPI.showMessageBox(options)
```

## 📦 构建和分发

### 本地构建

```bash
npm run build
```

构建产物位于 `dist-electron/` 目录。

### 代码签名

需要 Apple Developer 账号：

```bash
# 设置签名配置
export CSC_LINK_NAME="Developer ID Application: Your Name"
export CSC_KEY_PASSWORD="your-password"

# 构建签名版本
npm run build
```

### 公证

构建后需要公证以避免 Gatekeeper 警告：

```bash
# 使用 xcrun 公证
xcrun altool --notarize-app \
  --primary-bundle-id "com.minecontext.glass" \
  --username "your@apple.id" \
  --password "@keychain:AC_PASSWORD" \
  --file dist-electron/MineContext\ Glass.app
```

## 🐛 故障排除

### 常见问题

**Q: Electron 应用无法启动**
```bash
# 检查 Node.js 版本
node --version  # 需要 v18+

# 检查依赖安装
npm list electron
```

**Q: Python 后端启动失败**
```bash
# 检查 uv 环境
uv --version

# 检查 Python 依赖
uv sync
```

**Q: 前端无法连接后端**
- 检查后端进程是否正常启动
- 检查端口是否被占用
- 查看 Electron 主进程日志

**Q: 构建失败**
```bash
# 清理缓存
npm run clean
npm cache clean --force
```

### 调试模式

开发模式下会自动打开开发者工具。

手动开启开发者工具：
```javascript
// 在 electron/main.js 中
mainWindow.webContents.openDevTools();
```

## 📊 性能优化

### 内存使用优化
- 及时清理不必要的进程
- 优化前端资源加载
- 监控 Python 内存泄漏

### 启动时间优化
- 并行启动前后端
- 预加载常用资源
- 优化 Python 导入

### 包大小优化
- Tree-shaking 移除未使用代码
- 压缩图片和静态资源
- 优化 Python 依赖

## 🔄 热重载

开发模式下支持热重载：

- **前端**: Vite 自动重载
- **Electron**: 安装 `electron-reload` 支持主进程重载
- **后端**: 需要手动重启（开发时）

## 📚 相关文档

- [Electron 官方文档](https://www.electronjs.org/)
- [React 开发指南](webui/README.md)
- [OpenContext API 文档](docs/api/)
- [macOS 应用分发指南](docs/guides/macos-distribution.md)

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

---

**🎉 开始你的 Electron 开发之旅！**