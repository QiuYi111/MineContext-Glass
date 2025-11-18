# Frontend + Glass Backend Integration Plan

## 🎯 Project Overview

MineContext Glass 是一个"眼镜优先的个人上下文平台"，将日常生活的视频流转化为可组织的知识库。本文档详细分析了将glass模块后端接入frontend应用的开发计划，最终目标是通过Electron封装为macOS应用。

## 📊 Current Architecture Analysis

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │  Glass Backend  │    │   OpenContext   │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   Framework     │
│                 │    │                 │    │                 │
│ • TypeScript    │    │ • Video Upload  │    │ • Context Mgmt  │
│ • Vite          │    │ • Timeline API  │    │ • Storage       │
│ • Radix UI      │    │ • Report Gen    │    │ • AI Services   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack

**Frontend (`frontend/`)**
- React 18.3.1 + TypeScript
- Vite 6.3.5 (build tool & dev server)
- Radix UI + Tailwind CSS (UI components)
- 状态机导航模式 (无传统路由)

**Glass Backend (`opencontext/server/routes/glass.py`)**
- FastAPI REST API
- 完整的端点实现：上传、状态查询、报告生成
- 服务依赖注入模式
- 与OpenContext框架深度集成

**Desktop Application (`electron/main.js`)**
- Electron跨平台框架
- 自动端口检测
- Python后端进程管理
- 开发/生产环境适配

## 🔍 Integration Complexity Analysis

### Backend API Status: ✅ PRODUCTION READY

**完整的API端点实现：**
```python
# opencontext/server/routes/glass.py
@router.post("/upload")                    # 视频上传
@router.get("/timelines")                  # 时间线列表
@router.get("/status/{timeline_id}")       # 处理状态
@router.get("/report/{timeline_id}")       # 日报获取
@router.put("/report/{timeline_id}")       # 保存编辑
@router.post("/report/{timeline_id}/generate") # 重新生成
```

**服务层设计：**
```python
# 服务依赖注入模式
GlassIngestionService      # 视频处理服务
GlassContextRepository     # 数据存储服务
DailyReportService         # 报告生成服务
```

### Frontend Architecture: 🟡 SIMPLE BUT EFFECTIVE

**当前状态：**
- 86个TypeScript文件，代码质量良好
- 基于状态机的页面导航：`useState<Page>("welcome")`
- 组件化设计，职责分离清晰
- 无传统路由系统，但易于扩展

**集成优势：**
- App.tsx采用状态机模式，易于添加新页面
- 现有的FileUploadScreen、ProcessingScreen可直接复用
- 统一的错误处理和状态管理机制

## 🚀 Development Plan

### Phase 1: API Client Layer (0.5人日)

**目标：** 建立前端到glass后端的HTTP通信

**文件结构：**
```
frontend/src/api/
├── glass.ts           # Glass API客户端
├── types.ts           # TypeScript接口定义
└── utils.ts           # HTTP工具函数
```

**实现要点：**
```typescript
// 环境感知的API路由 (复用webui模式)
function buildUrl(path: string): string {
  if (isElectronEnvironment()) {
    const backendBase = getBackendBase();
    return `${backendBase}${path}`;
  } else {
    return path; // Vite代理处理
  }
}

// 核心API方法
export async function uploadVideo(file: File): Promise<UploadResponse>
export async function fetchTimelines(): Promise<Timeline[]>
export async function fetchStatus(timelineId: string): Promise<ProcessingStatus>
export async function fetchDailyReport(timelineId: string): Promise<DailyReport>
```

### Phase 2: Vite Proxy Configuration (0.25人日)

**目标：** 开发环境API代理配置

**配置修改：**
```typescript
// frontend/vite.config.ts
export default defineConfig({
  server: {
    port: 5175, // 避免与webui冲突
    proxy: {
      "/glass": {
        target: process.env.VITE_GLASS_API_PROXY ?? "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
```

### Phase 3: Core Components Development (1.5人日)

**目标：** 开发glass功能的核心UI组件

**组件结构：**
```
frontend/src/components/glass/
├── GlassUploadScreen.tsx     # 视频上传界面
├── GlassTimelineScreen.tsx   # 时间线管理
├── GlassReportScreen.tsx     # 报告查看器
└── GlassStatusMonitor.tsx    # 处理状态监控
```

**复用策略：**
- `GlassUploadScreen` → 扩展现有`FileUploadScreen`
- `GlassStatusMonitor` → 复用`ProcessingScreen`逻辑
- 新增时间线管理和报告查看组件

### Phase 4: State Management Integration (0.75人日)

**目标：** 将glass功能集成到现有状态机

**状态扩展：**
```typescript
type Page =
  | Page // 现有页面类型
  | "glass-upload"           // glass视频上传
  | "glass-timeline"         // glass时间线管理
  | "glass-report"           // glass报告查看
  | "glass-status";          // glass处理状态

// 状态管理扩展
const [glassData, setGlassData] = useState<{
  timelines: Timeline[];
  currentReport: DailyReport | null;
  uploadStatus: ProcessingStatus | null;
}>({ timelines: [], currentReport: null, uploadStatus: null });
```

### Phase 5: Navigation Integration (0.5人日)

**目标：** 在现有导航中添加glass入口

**集成点：**
- HomeScreen：添加"Glass Context"入口按钮
- TabBar：可选的glass专用tab
- QuickNav：glass相关页面的快速导航

## 📱 Electron Integration Strategy

### Current Electron Architecture

**入口文件：** `electron/main.js`
```javascript
// 现有功能
- Python后端进程管理 (OpenContext server)
- 端口自动检测和配置
- 开发/生产环境切换
- 安全的进程通信
```

### Glass Integration Requirements

**1. 进程管理扩展**
```javascript
// 确保Glass服务启动
async function startBackend() {
  const serverProcess = spawn('uv', ['run', 'opencontext', 'start', ...args]);

  // 添加glass特定健康检查
  await checkGlassHealth();
}
```

**2. 端口配置**
```javascript
// 玻璃后端与OpenContext共享同一端口
const BACKEND_PORT = 8000;
const FRONTEND_PORT = 5175; // frontend专用端口
```

**3. 构建配置**
```javascript
// package.json scripts
{
  "electron-dev": "concurrently \"npm run dev:frontend\" \"npm run dev:backend\" \"wait-on http://127.0.0.1:8000 && electron .\"",
  "build": "npm run build:frontend && npm run build:electron",
  "dist": "npm run build && electron-builder"
}
```

## ⏱️ Time Estimation & Risk Assessment

### Total Estimation: 3.5人日 (85% Confidence Interval)

| Phase | Estimation | Confidence | Risk Level | Key Dependencies |
|-------|------------|------------|------------|------------------|
| API Client Layer | 0.5人日 | 95% | Low | webui reference implementation |
| Vite Proxy Config | 0.25人日 | 99% | Very Low | Standard configuration |
| Core Components | 1.5人日 | 80% | Medium | UI complexity requirements |
| State Management | 0.75人日 | 90% | Low | Simple extension |
| Navigation Integration | 0.5人日 | 95% | Low | Standard React patterns |

### Risk Assessment: LOW RISK PROJECT

**🟢 Technical Risks (Low)**
- **Backend API Maturity**: glass.py已完全实现并通过测试
- **Integration Pattern Clarity**: webui提供完整的参考实现
- **Frontend Architecture Simplicity**: 状态机模式易于扩展

**🟡 Dependency Risks (Medium)**
- **AUC Turbo API**: 需要有效的语音识别凭据
- **FFmpeg Dependency**: 系统需要安装FFmpeg
- **Port Conflicts**: 默认8000端口可能被占用

**🟢 Compatibility Risks (Low)**
- **Existing Functionality Preservation**: 独立模块集成，不影响现有功能
- **Electron Compatibility**: 与现有打包流程完全兼容
- **Browser Compatibility**: 基于标准Web API

### Success Factors & Mitigation

**Critical Success Factors:**
1. **Environment Setup**: AUC credentials和FFmpeg可用性
2. **Port Management**: 确保backend/frontend端口不冲突
3. **API Consistency**: 前后端接口定义保持一致

**Mitigation Strategies:**
```bash
# 环境检查脚本
#!/bin/bash
# check-environment.sh

if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ERROR: FFmpeg not found in PATH"
    exit 1
fi

if [[ -z "$AUC_APP_KEY" || -z "$AUC_ACCESS_KEY" ]]; then
    echo "❌ ERROR: AUC credentials not set"
    echo "Please set: export AUC_APP_KEY=your-key && export AUC_ACCESS_KEY=your-secret"
    exit 1
fi

# 检查端口可用性
if lsof -i :8000 &> /dev/null; then
    echo "⚠️  WARNING: Port 8000 is in use"
fi

echo "✅ Environment check passed"
```

## 🎯 Final Target: macOS .app Package

### Build Process Flow

```
1. Frontend Build:    npm run build          (React → static files)
2. Backend Package:   ./build.sh             (Python → executable)
3. Electron Build:    npm run dist           (All-in-one .app)
4. Code Signing:      codesign --force       (macOS distribution)
```

### Directory Structure (Final .app)

```
MineContext Glass.app/
├── Contents/
│   ├── Info.plist
│   ├── MacOS/
│   │   └── MineContext Glass    # Electron main + bundled Python
│   ├── Resources/
│   │   ├── app.icns             # Application icon
│   │   └── dist/                # Frontend build assets
│   └── Frameworks/
│       └── [Python runtime]
```

### Key Configuration Files

**package.json (Electron Builder)**
```json
{
  "build": {
    "appId": "com.minecontext.glass",
    "productName": "MineContext Glass",
    "directories": {
      "output": "dist-electron"
    },
    "files": [
      "electron/main.js",
      "frontend/dist/**/*",
      "dist/main/**/*"
    ],
    "mac": {
      "category": "public.app-category.productivity",
      "icon": "assets/app.icns",
      "hardenedRuntime": true,
      "entitlements": "assets/entitlements.mac.plist"
    }
  }
}
```

**Entitlements (Security & Sandbox)**
```xml
<!-- assets/entitlements.mac.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
</dict>
</plist>
```

## 🏆 Expected Deliverables

### Development Milestones

**Milestone 1 (Day 1): API Integration**
- [ ] Glass API客户端完成
- [ ] Vite代理配置就绪
- [ ] 基础视频上传功能测试通过

**Milestone 2 (Day 2): Core Features**
- [ ] 时间线管理组件完成
- [ ] 报告查看器实现
- [ ] 状态监控集成

**Milestone 3 (Day 3): Navigation & Polish**
- [ ] 完整的导航集成
- [ ] 错误处理优化
- [ ] 用户体验优化

**Milestone 4 (Day 3.5): Electron Packaging**
- [ ] 构建脚本更新
- [ ] .app打包测试
- [ ] 分发包准备

### Final Application Features

**Core Functionality:**
- ✅ 视频文件上传和处理
- ✅ 实时处理状态监控
- ✅ 时间线管理和浏览
- ✅ 智能日报生成和查看
- ✅ 跨平台桌面应用支持

**Technical Excellence:**
- ✅ 类型安全的TypeScript实现
- ✅ 响应式UI设计
- ✅ 错误处理和用户反馈
- ✅ 本地优先的数据处理
- ✅ macOS应用签名和分发

## 📋 Implementation Checklist

### Pre-Development Setup
- [ ] AUC Turbo API credentials configured
- [ ] FFmpeg installed and accessible
- [ ] Python dependencies installed via `uv sync`
- [ ] Node.js dependencies installed via `npm install`

### Development Tasks
- [ ] Create `frontend/src/api/glass.ts`
- [ ] Configure Vite proxy for `/glass` endpoints
- [ ] Implement `GlassUploadScreen` component
- [ ] Implement `GlassTimelineScreen` component
- [ ] Implement `GlassReportScreen` component
- [ ] Add glass pages to App.tsx state machine
- [ ] Update electron/main.js for frontend integration
- [ ] Test end-to-end functionality

### Build & Distribution
- [ ] Update build scripts for multi-component architecture
- [ ] Configure Electron Builder settings
- [ ] Test .app packaging process
- [ ] Verify code signing and notarization
- [ ] Test on clean macOS environment

---

**Project Complexity:** 🟡 Low-to-Medium
**Estimated Timeline:** 3.5人日
**Risk Level:** 🟢 Low Risk
**Success Probability:** 85%

This integration represents a textbook example of connecting two well-designed systems with clear interfaces and mature architectures. The primary challenges are environmental setup and configuration rather than complex algorithmic problems.