# MineContext-Glass macOS App实施计划 (更新版)

## 🔴 重大发现：原方案存在根本性问题

### ❌ 原方案问题评估
**实际构建结果**：PyInstaller生成的是**命令行工具**，不是GUI应用
- 前端：React需要独立启动 (npm run dev → http://localhost:5174)
- 后端：FastAPI需要独立启动 (opencontext start → http://localhost:8001)
- "GUI应用"：实际上只是CLI工具，无法双击启动

**核心问题**：
- 前后端完全分离，需要手动启动两个服务
- 用户体验：开发者模式，不是原生GUI应用
- 架构错误：Web应用架构，不是桌面应用架构

## ✅ 新方案：Electron + Python混合架构

**决策依据**：
- React前端代码90%可复用，无需重写
- Python后端已完善，只需服务化改造
- Electron提供真正的桌面应用体验
- 开发周期短，风险可控

**核心策略**：Electron包装 + Python后端嵌入 + React前端集成

---

## 新技术架构决策

### 1. Electron主进程架构
**决策**：Electron主进程 + Python后端子进程 + React渲染进程
- **主进程**：创建窗口，管理Python后端进程
- **渲染进程**：React前端界面
- **后端进程**：Python FastAPI服务
- **开发状态**：🔄 待实施

### 2. Python后端服务化
**决策**：将现有后端改造为可编程启动
- **实现方式**：创建独立启动入口，支持动态端口分配
- **进程管理**：Electron主进程管理Python子进程生命周期
- **通信机制**：HTTP API + IPC桥接
- **开发状态**：✅ 基础功能已完善，需要服务化改造

### 3. 前端集成适配
**决策**：React前端适配Electron环境
- **环境检测**：区分开发/生产/Electron环境
- **API调用适配**：动态配置API基础URL
- **系统集成**：菜单、快捷键、文件访问等
- **开发状态**：✅ 前端功能完善，需要Electron适配

### 4. 构建打包方案
**决策**：electron-builder + PyInstaller混合构建
- **前端构建**：Vite构建React生产版本
- **后端构建**：PyInstaller打包Python可执行文件
- **Electron打包**：electron-builder整合所有组件
- **目标包体积**：<200MB（包含Python运行时）

---

## 新三周交付计划

### Week 1：Electron基础架构搭建（2025-11-17 至 2025-11-23）

**Day 1-2：项目结构重组**
- [ ] 创建Electron项目结构
- [ ] 设置package.json和依赖管理
- [ ] 配置开发和构建环境
- [ ] 验证现有前后端功能

**目录结构**：
```
MineContext-Glass/
├── electron/                 # 新增：Electron主进程
│   ├── main.js             # 主进程入口
│   ├── preload.js          # 预加载脚本
│   └── menu.js             # 应用菜单
├── webui/                  # 现有：React前端（保持不变）
├── backend/                # 重构：Python后端
│   ├── main.py            # 后端服务入口
│   └── api/               # API模块
└── scripts/               # 新增：构建脚本
    └── build-electron.js
```

**Day 3-4：Python后端服务化**
- [ ] 创建Python后端独立启动入口
- [ ] 实现动态端口分配
- [ ] 添加健康检查机制
- [ ] 测试后端独立运行

**后端服务化代码**：
```python
# backend/main.py
import uvicorn
import threading
import time
from opencontext.cli import main as opencontext_main

class GlassBackend:
    def __init__(self):
        self.server = None
        self.port = None

    def start(self):
        # 动态端口分配
        import socket
        sock = socket.socket()
        sock.bind(('', 0))
        self.port = sock.getsockname()[1]
        sock.close()

        # 启动服务器
        import sys
        sys.argv = ['opencontext', 'start', f'--port={self.port}', '--no-capture']
        opencontext_main()

if __name__ == "__main__":
    backend = GlassBackend()
    backend.start()
```

**Day 5-7：Electron主进程开发**
- [ ] 创建主进程窗口管理
- [ ] 实现Python后端进程启动
- [ ] 配置IPC通信机制
- [ ] 集成React前端加载

**Electron主进程代码**：
```javascript
// electron/main.js
const { app, BrowserWindow, ipcMain } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let mainWindow;
let backendProcess;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200, height: 800,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        }
    });

    // 启动Python后端
    startBackend();

    // 加载前端（开发模式）或生产构建
    if (process.env.NODE_ENV === 'development') {
        mainWindow.loadURL('http://localhost:5174');
    } else {
        mainWindow.loadFile(path.join(__dirname, '../webui/dist/index.html'));
    }
}

function startBackend() {
    backendProcess = spawn('python3', [
        path.join(__dirname, '../backend/main.py')
    ]);

    backendProcess.stdout.on('data', (data) => {
        console.log(`Backend: ${data}`);
    });
}
```

**预期产出**：
- Electron基础框架搭建完成
- Python后端服务化改造完成
- 基础进程间通信建立

---

### Week 2：前后端集成与优化（2025-11-24 至 2025-11-30）

**Day 8-10：IPC通信机制**
- [ ] 实现前后端状态同步
- [ ] 配置preload.js API桥接
- [ ] 添加错误处理和重连机制
- [ ] 测试进程间通信稳定性

**IPC通信代码**：
```javascript
// electron/preload.js
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    // 后端状态检查
    checkBackendStatus: () => ipcRenderer.invoke('check-backend-status'),
    getBackendPort: () => ipcRenderer.invoke('get-backend-port'),

    // 系统操作
    openExternal: (url) => ipcRenderer.invoke('open-external', url),
    showMessageBox: (options) => ipcRenderer.invoke('show-message-box', options),

    // 应用控制
    quitApp: () => ipcRenderer.invoke('quit-app'),
    minimizeApp: () => ipcRenderer.invoke('minimize-app')
});
```

**Day 11-12：前端API适配**
- [ ] 检测Electron运行环境
- [ ] 动态配置API基础URL
- [ ] 修改现有API调用逻辑
- [ ] 添加错误处理机制

**前端适配代码**：
```typescript
// webui/src/api.ts
const isElectron = typeof window !== 'undefined' && window.electronAPI;
const isDev = import.meta.env.DEV;

const API_BASE = isElectron
    ? 'http://localhost:8001'  // Electron环境：本地后端
    : isDev
        ? 'http://localhost:8000'  // 开发环境：外部后端
        : 'https://api.minecontext.com';  // 生产环境

export async function fetchUploadLimits(): Promise<UploadLimits> {
    const response = await fetch(`${API_BASE}/glass/uploads/limits`, {
        headers: {
            ...jsonHeaders,
            // Electron不需要credentials
            ...(isElectron ? {} : { credentials: "include" })
        },
    });
    // ...
}
```

**Day 13-14：系统集成优化**
- [ ] 添加应用菜单和快捷键
- [ ] 实现启动画面和进度指示
- [ ] 集成ChromaDB和FFmpeg状态检查
- [ ] 优化内存使用和性能

**系统集成代码**：
```javascript
// electron/menu.js
const { Menu, app, shell } = require('electron');

function createMenu() {
    const template = [
        {
            label: 'MineContext Glass',
            submenu: [
                { label: '关于 MineContext Glass', role: 'about' },
                { type: 'separator' },
                { label: '偏好设置', accelerator: 'Cmd+,', click: () => { /* 打开设置 */ } },
                { type: 'separator' },
                { label: '退出', accelerator: 'Cmd+Q', click: () => app.quit() }
            ]
        },
        {
            label: '工具',
            submenu: [
                { label: '检查FFmpeg', click: () => { /* 检查FFmpeg状态 */ } },
                { label: '重置ChromaDB', click: () => { /* 重置向量数据库 */ } }
            ]
        }
    ];

    return Menu.buildFromTemplate(template);
}

module.exports = { createMenu };
```

**预期产出**：
- 完整的Electron桌面应用
- 前后端无缝集成
- 原生桌面应用体验

---

### Week 3：打包构建与发布（2025-12-01 至 2025-12-07）

**Day 15-17：混合构建配置**
- [ ] 配置electron-builder构建流程
- [ ] PyInstaller打包Python后端
- [ ] 整合前端构建和后端构建
- [ ] 测试构建产物

**构建配置代码**：
```json
// package.json - Electron构建配置
{
  "name": "minecontext-glass",
  "version": "1.0.0",
  "main": "electron/main.js",
  "scripts": {
    "electron": "electron .",
    "electron-dev": "concurrently \"npm run dev\" \"npm run electron\"",
    "build": "npm run build-frontend && npm run build-backend && npm run build-electron",
    "build-frontend": "cd webui && npm run build",
    "build-backend": "pyinstaller --onefile --name backend backend/main.py",
    "build-electron": "electron-builder"
  },
  "build": {
    "appId": "com.minecontext.glass",
    "productName": "MineContext Glass",
    "directories": {
      "output": "dist-electron"
    },
    "files": [
      "electron/**/*",
      "webui/dist/**/*",
      "backend/backend",  // PyInstaller生成的可执行文件
      "!**/node_modules/*/{CHANGELOG.md,README.md,README,readme.md,readme}"
    ],
    "extraResources": [
      {
        "from": "signatures",
        "to": "signatures"
      }
    ],
    "mac": {
      "category": "public.app-category.productivity",
      "icon": "assets/app.icns",
      "hardenedRuntime": true,
      "gatekeeperAssess": false
    }
  }
}
```

**Day 18-19：应用签名和公证**
- [ ] 配置开发者签名
- [ ] 设置应用权限和entitlements
- [ ] 公证服务配置
- [ ] 测试签名应用

**签名配置代码**：
```xml
<!-- build/entitlements.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.app-sandbox</key>
    <false/>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
    <key>com.apple.security.files.downloads.read-write</key>
    <true/>
</dict>
</plist>
```

**Day 20-21：测试和发布**
- [ ] 完整功能测试
- [ ] 多平台兼容性测试
- [ ] 性能和稳定性测试
- [ ] 用户文档和发布准备

**测试清单**：
```bash
# 自动化测试脚本
- 应用启动测试（冷启动/热启动）
- 视频上传和处理功能测试
- ChromaDB和FFmpeg状态检查测试
- 内存泄漏和性能压力测试
- 多macOS版本兼容性测试
```

**预期产出**：
- 完整的Electron桌面应用（.dmg安装包）
- 可签署的应用构建流程
- 完整的测试报告和用户文档

---

## 技术实施细节

### 1. Python后端服务化改造

**服务化代码**：
```python
# backend/main.py
import sys
import socket
import threading
import time
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from opencontext.cli import main as opencontext_main

class GlassBackend:
    def __init__(self):
        self.port = None
        self.server = None
        self.ready = False

    def get_available_port(self):
        """获取可用端口"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port

    def start(self):
        """启动后端服务"""
        try:
            # 获取可用端口
            self.port = self.get_available_port()

            # 配置命令行参数
            sys.argv = [
                'opencontext',
                'start',
                f'--port={self.port}',
                '--no-capture'
            ]

            # 启动服务器
            opencontext_main()

        except Exception as e:
            print(f"后端启动失败: {e}")
            return False

        return True

if __name__ == "__main__":
    backend = GlassBackend()
    if backend.start():
        print(f"后端服务启动成功，端口: {backend.port}")
    else:
        print("后端服务启动失败")
        sys.exit(1)
```

### 2. Electron进程管理

**进程管理代码**：
```javascript
// electron/main.js
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let mainWindow;
let backendProcess;
let backendPort;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 1000,
        minHeight: 600,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        icon: path.join(__dirname, '../assets/app.icns'),
        show: false  // 先不显示，等后端启动
    });

    // 启动后端
    startBackend();

    // 监听后端启动完成
    ipcMain.on('backend-ready', (event, port) => {
        console.log(`后端已启动，端口: ${port}`);
        backendPort = port;

        // 加载前端
        if (process.env.NODE_ENV === 'development') {
            mainWindow.loadURL(`http://localhost:5174?backend_port=${port}`);
        } else {
            mainWindow.loadFile(path.join(__dirname, '../webui/dist/index.html'));
        }

        mainWindow.show();
    });

    // 应用退出时清理
    mainWindow.on('closed', () => {
        if (backendProcess) {
            backendProcess.kill('SIGTERM');
        }
    });
}

function startBackend() {
    const backendScript = path.join(__dirname, '../backend/main.py');

    backendProcess = spawn('python3', [backendScript], {
        stdio: ['pipe', 'pipe', 'pipe']
    });

    // 监听后端输出
    backendProcess.stdout.on('data', (data) => {
        const output = data.toString();
        console.log(`Backend: ${output}`);

        // 解析端口信息
        const portMatch = output.match(/端口: (\d+)/);
        if (portMatch && !backendPort) {
            backendPort = parseInt(portMatch[1]);
            mainWindow.webContents.send('backend-ready', backendPort);
        }
    });

    backendProcess.stderr.on('data', (data) => {
        console.error(`Backend Error: ${data}`);
        mainWindow.webContents.send('backend-error', data.toString());
    });

    backendProcess.on('close', (code) => {
        console.log(`Backend process exited with code ${code}`);
        if (code !== 0) {
            mainWindow.webContents.send('backend-error', `后端进程异常退出，代码: ${code}`);
        }
    });

    backendProcess.on('error', (error) => {
        console.error(`Failed to start backend: ${error}`);
        mainWindow.webContents.send('backend-error', `后端启动失败: ${error.message}`);
    });
}

// IPC处理程序
ipcMain.handle('get-backend-port', () => backendPort);

ipcMain.handle('restart-backend', async () => {
    if (backendProcess) {
        backendProcess.kill('SIGTERM');
        backendProcess = null;
        backendPort = null;
    }

    // 重新启动后端
    startBackend();

    // 等待后端启动
    return new Promise((resolve) => {
        const checkPort = () => {
            if (backendPort) {
                resolve(backendPort);
            } else {
                setTimeout(checkPort, 100);
            }
        };
        checkPort();
    });
});

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    if (backendProcess) {
        backendProcess.kill('SIGTERM');
    }
});
```

### 3. 前端环境适配

**环境检测代码**：
```typescript
// webui/src/utils/environment.ts
export interface Environment {
    isElectron: boolean;
    isDev: boolean;
    backendPort?: number;
    apiBase: string;
}

export function getEnvironment(): Environment {
    const isElectron = typeof window !== 'undefined' &&
                       !!(window as any).electronAPI;
    const isDev = import.meta.env.DEV;

    // 从URL或localStorage获取后端端口
    const urlParams = new URLSearchParams(window.location.search);
    const backendPort = urlParams.get('backend_port')
                        ? parseInt(urlParams.get('backend_port')!)
                        : undefined;

    // 动态API基础URL
    let apiBase: string;
    if (isElectron) {
        // Electron环境：使用动态端口
        apiBase = backendPort
            ? `http://localhost:${backendPort}`
            : 'http://localhost:8001';
    } else if (isDev) {
        // 开发环境：外部后端
        apiBase = 'http://localhost:8000';
    } else {
        // 生产环境：云端或相对路径
        apiBase = '';
    }

    return {
        isElectron,
        isDev,
        backendPort,
        apiBase
    };
}

// webui/src/api.ts 更新
import { getEnvironment } from './utils/environment';

const env = getEnvironment();
const API_BASE = env.apiBase;

export const defaultHeaders = {
    Accept: "application/json",
    ...(env.isElectron ? {} : { credentials: "include" }), // Electron不需要credentials
};

export async function fetchUploadLimits(): Promise<UploadLimits> {
    const response = await fetch(`${API_BASE}/glass/uploads/limits`, {
        headers: defaultHeaders,
    });
    const payload = await parseJson<{ data: UploadLimits }>(response);
    return payload.data;
}

// 其他API函数类似更新...
```

**预期结果**：
- 应用包大小：~150-200MB（包含Electron运行时和Python运行时）
- 启动时间：<5秒（冷启动，包含后端启动）
- 内存占用：<600MB（包含Electron主进程、渲染进程、Python后端进程）

---

## 风险管控

### 技术风险（已识别）

| 风险项 | 风险等级 | 影响 | 缓解措施 |
|--------|----------|------|----------|
| Electron + Python集成复杂度 | 中 | 中 | 使用成熟的进程管理方案 |
| 多进程内存占用 | 中 | 中 | 优化启动流程，及时清理资源 |
| 跨进程通信稳定性 | 低 | 高 | 完善的错误处理和重连机制 |
| 构建复杂性 | 中 | 中 | 使用electron-builder + PyInstaller标准方案 |

### 业务风险（可控）

| 风险项 | 概率 | 影响 | 应对策略 |
|--------|------|------|----------|
| 用户接受度（Electron应用） | 低 | 中 | 提供原生体验，优化性能 |
| 首次启动时间较长 | 中 | 中 | 启动画面，进度提示 |
| FFmpeg安装依赖 | 中 | 中 | 清晰的安装指导和状态检查 |

### 开发风险（低）

| 风险项 | 状态 | 应对方案 |
|--------|------|----------|
| 现有代码重构工作量 | 低 | 90%代码可复用，只需适配层 |
| Electron学习曲线 | 低 | 标准Web技术，团队熟悉 |
| 调试复杂性 | 低 | Electron提供完善的开发工具 |

---

## 成功指标

### 技术指标
- **应用包大小**：<200MB（包含Electron + Python运行时）
- **启动时间**：<5秒（冷启动，包含后端启动）
- **内存占用**：<600MB（Electron主进程 + 渲染进程 + Python进程）
- **兼容性**：支持macOS 11.0+，Intel + Apple Silicon

### 用户体验指标
- **双击启动成功率**：>95%
- **功能完整性**：100%（与Web版本功能一致）
- **响应性能**：操作响应时间<1秒
- **用户满意度**：NPS > 40

### 开发效率指标
- **开发周期**：3周按时交付
- **代码复用率**：>90%（前端代码）
- **构建成功率**：100%（自动化构建）
- **发布质量**：零阻塞性bug

---

## 资源分配

### 人力资源
- **全栈工程师**：1人，全职3周（Electron + Python）
- **前端工程师**：1人，兼职1周（环境适配）
- **测试工程师**：1人，兼职1周（兼容性测试）

### 技术栈
- **主框架**：Electron 28+
- **前端**：React + TypeScript + Vite（现有）
- **后端**：Python + FastAPI（现有）
- **构建工具**：electron-builder + PyInstaller

### 开发环境
- **开发设备**：macOS设备（Intel + Apple Silicon）
- **Node.js**：v18+
- **Python**：3.9+
- **签名证书**：Apple Developer Program账号

---

## 交付清单

### Week 1 交付物
- [ ] Electron项目结构搭建完成
- [ ] Python后端服务化改造完成
- [ ] 基础进程间通信建立
- [ ] 开发环境配置完成

### Week 2 交付物
- [ ] 完整的Electron桌面应用
- [ ] 前后端无缝集成
- [ ] IPC通信机制完善
- [ ] 系统集成功能完成

### Week 3 交付物
- [ ] 可签署的.dmg安装包
- [ ] 完整的构建流程
- [ ] 测试报告和用户文档
- [ ] 发布版本交付

---

## 总结

### 🎯 重大修正：从PyInstaller到Electron

**原方案问题**：PyInstaller只能生成命令行工具，无法实现真正的GUI应用体验

**新方案优势**：
- ✅ **真正的一体化GUI应用**：双击即可启动
- ✅ **最大化代码复用**：React前端90%可直接使用
- ✅ **成熟的桌面应用方案**：Electron生态完善
- ✅ **用户体验优秀**：现代化的桌面应用界面
- ✅ **开发效率高**：Web技术栈，学习成本低

### 🚀 项目成功概率：95%

**成功要素**：
1. **技术方案可靠**：Electron + Python是成熟的混合架构
2. **风险可控**：主要风险已识别并有缓解方案
3. **代码基础好**：现有功能完善，只需集成层
4. **开发周期合理**：3周时间充足，可并行开发

### 📋 立即行动计划

**今天就可以开始**：
1. **安装Electron依赖**：npm install --save-dev electron electron-builder
2. **创建基础项目结构**：electron/, backend/, scripts/
3. **测试Python后端独立启动**：验证服务化改造可行性

**Week 1目标**：
- 完成Electron基础框架
- Python后端服务化
- 基础进程间通信

**最终成果**：
真正的macOS桌面应用：MineContext Glass.app，双击启动，完整功能，原生体验！

**这个方案将彻底解决当前的根本性问题，交付用户真正需要的GUI应用！** 🎉