# Glass WebUI PRD — Daily Report First

## 最新更新摘要（2025-10-29）
- **已完成**：`glass/webui` 独立 Vite + React 工程上线；炫酷玻璃拟态 UI、上传/轮询/Markdown 编辑链路、Highlights/Visual Cards 等核心模块全部跑通。MineContext 内置 `/glass` 页面改为提示说明，后端新增 `/glass/uploads/limits`、`/glass/report/{id}` 等接口并完成 Markdown sanitise 与持久化。
- **新增诉求**：
  1. 将后端精简为与 `glass start` CLI 同等的轻量服务：只保留视频 ingestion → 对齐 → 报告生成链路，无需依赖 OpenContext 其他模块或胖配置。
  2. 在仪表盘显眼位置加入 **“Generate Daily Report” 按钮**，行为类似 OpenContext 的生成入口：显式触发生成流程、带动效与状态反馈。
- **下一步**：保留现有 REST 契约，增加 Demo/Mock 驱动层、生成 CTA 与 README 指南，并对 UI 状态管理进行增强。

## 0. 前置拷问
- **真问题吗？** 用户已经在用 `glass start` 生成时间线，却没有一个能直接消费产出的前端，日报成品还得手写，这是实打实的痛点。
- **有更简单的方法吗？** React + 状态机前端搭配现有 `/glass` API，增量补齐必要后端接口即可，不需要推翻 MineContext Web 框架。
- **会破坏什么吗？** 保留现有 CGI 模板入口，新增前端走独立 bundle，所有新 API 均为 `/glass/*` 前缀并纯新增字段，旧用户毫发无损。

## 1. 目标与不做的事
- **目标**
  - 让上传→处理→生成日报的全链路在 WebUI 中一站式完成。
  - 日报以 Markdown 为核心，支持系统自动稿和人工修订并行存在。
  - 视觉基调「极简、精致」：黑白为主、单一强调色、严控视觉噪音。
- **不做**
  - 不引入复杂富文本或所见即所得编辑器。
  - 不在前端直接展示原始 manifest 细节。
  - 不修改旧 MineContext 页面路由与静态资源。

## 2. 角色与场景
- **记录者（Uploader）**：上传第一视角视频，关注进度反馈、失败原因。
- **分析师（Reporter）**：在处理完成后查看自动生成日报、快速增删段落、补充高光。
- **审批者（Reviewer）**：查看最终日报的 Markdown 渲染，对安全和一致性敏感。

场景按时间排序：
1. 上传者拖拽/选择视频，前端即时校验文件类型/体积，后台异步处理。
2. 处理阶段自动轮询状态，完成后一次性拉取 `DailyReportEnvelope`。
3. 分析师在同一界面编辑 Markdown，实时预览与自动摘要对照。
4. 保存手动修改后，审批者打开页面即看渲染后的日报版本。

## 3. 数据结构与后端接口
### 3.1 新/扩展接口
| Method | Path | 说明 |
| --- | --- | --- |
| GET | `/glass/uploads/limits` | 返回 `max_size_mb`, `allowed_types`, `max_concurrent`，前端做预检。 |
| POST | `/glass/upload` | 现有接口，不变。 |
| GET | `/glass/status/{timeline_id}` | 现有接口，不变。 |
| GET | `/glass/context/{timeline_id}` | 扩展返回字段：`summary`, `highlights`, `visual_cards`, `daily_report.auto_markdown`。 |
| GET | `/glass/report/{timeline_id}` | 返回 `DailyReportEnvelope`。 |
| PUT | `/glass/report/{timeline_id}` | 写入 `manual_markdown`、`manual_metadata`（例如 highlights 顺序）。 |

### 3.2 `DailyReportEnvelope` 定义
```json
{
  "timeline_id": "xxx",
  "source": "timeline/2025-01-12_demo.mp4",
  "auto_markdown": "...",
  "manual_markdown": "...",
  "rendered_html": "...",
  "highlights": [
    {
      "title": "关键操作",
      "timestamp": 123.4,
      "summary": "……",
      "modality": "frame",
      "thumbnail_url": "..."
    }
  ],
  "visual_cards": [
    {
      "image_url": "...",
      "caption": "……",
      "segment_start": 10.2,
      "segment_end": 12.7
    }
  ],
  "updated_at": "2025-01-12T08:23:54Z"
}
```
> `rendered_html` 为后端经 Markdown + Bleach 白名单 sanitise 的产物，前端仅用于展示。

### 3.3 存储扩展
- `glass_multimodal_context` 新增 `auto_summary_json`（可选）存放高光引用。
- 新建 `glass_daily_reports` 表：`timeline_id` 主键，`manual_markdown`, `manual_metadata`, `updated_at`。
- 通过 `ContextEnvelope` 构建每日摘要时写入 `auto_markdown` / `highlights`，与旧流程解耦。

## 4. 前端信息架构（React + Vite + TypeScript）
```
glass/webui/
├── src/
│   ├── app.tsx            # 顶级路由与状态提供
│   ├── state/glassStore.ts # Zustand 状态机：idle → uploading → processing → report_ready → error
│   ├── components/
│   │   ├── UploadPanel.tsx
│   │   ├── ProcessingStatus.tsx
│   │   ├── ReportEditor/
│   │   │   ├── EditorPane.tsx
│   │   │   ├── PreviewPane.tsx  # remark + rehype-sanitize
│   │   │   └── Toolbar.tsx
│   │   ├── HighlightsGrid.tsx
│   │   └── TimelineMeta.tsx
│   └── services/
│       ├── api.ts         # fetch 封装 + 指数退避轮询
│       └── markdown.ts    # 公共渲染/校验
└── public/index.html
```

- 状态变化只通过 `glassStore`，组件内不直接操作 DOM。
- 视觉规范：全局 12 列布局，留白 ≥ 32px，字体 `Inter`/`Noto Sans`，色板 `#101010`、`#6F6F6F`、强调色 `#0D6EFD`。
- 响应式：≥1200px 展示双栏；<900px 自动切换上下布局。

## 5. 交互与流程

### 5.1 上传阶段
1. 首屏展示上传卡片 + 报表列表（空态文案）。
2. 点击或拖拽触发 `handleFiles`：
   - 读取 `limits` 缓存，校验类型/大小/并发。
   - 不通过直接在反馈区域提示具体原因。
3. 合法文件调用 `api.upload(file)`，状态机转 `uploading`；显示进度条（读取 `UploadFile.read()` 字节进度）。
4. 成功后进入 `processing`，展示队列提示（含 `timeline_id`）。

### 5.2 处理阶段
- 状态机 `processing` 启动轮询：`3s→6s→12s→24s→48s`，最多 6 次。
- 任何请求失败均重试下一轮；超出上限进入 `error`，提示“后台继续处理”。
- 一旦 `status=completed`，状态机变 `report_ready`，缓存 `timeline_id`。

### 5.3 日报编辑
- `ReportEditor` 初始加载：
  - 左栏「自动摘要」（只读 Markdown）。
  - 中央「我的 Markdown」编辑框，预填自动摘要。
  - 右栏 `PreviewPane` 渲染实际效果。
- 编辑保存：
  - 点击保存 → PUT `/glass/report/{timeline_id}`。
  - 成功：更新本地 `manual_markdown` 与 `rendered_html`，显示 “保存于 HH:MM”。
  - 失败：保持旧值，提示错误并允许重试。
- 附加功能：
  - `Toolbar`: “插入时间戳”、“恢复自动稿”、“复制链接”。
  - Shortcuts：`Ctrl+S`/`Cmd+S` 触发保存。

### 5.4 高光与视觉卡片
- `HighlightsGrid` 展示最多 8 条关键片段，来源于 `highlights`。
- 点击高光时在 Markdown 中插入模板：
  ```
  ### 高光：{title}
  - 时间点：{timestamp}
  - 摘要：{summary}
  ```
- 视觉卡片只预览，不提供编辑；后续独立需求再加。

## 6. 安全与兼容
- 所有 Markdown 渲染在后端/前端双重 sanitise，允许标签 `["p","h1","h2","h3","h4","h5","h6","ul","ol","li","pre","code","blockquote","a","strong","em"]`。
- 上传接口开启文件名清洗与后缀白名单；`/glass/uploads/limits` 内 `allowed_types` 可热更新。
- 保留旧 HTML 模板，通过 `feature_flag_glass_react_ui` 控制入口；默认新 UI。
- CLI、API 客户端完全不受影响。

## 7. 验收标准
1. `uv run opencontext start --config ...` 启动后访问 `/glass`，默认加载 React 日报界面。
2. 上传 ≤限制的视频，完成处理，页面展示自动日报并可编辑 Markdown。
3. 编辑 Markdown 并保存，刷新页面仍能看到修订版，同时自动摘要保留原样。
4. Playwright 测试覆盖：
   - 上传失败提示；
   - 轮询超时回退；
   - Markdown 保存后预览匹配。
5. 手动跑 10 分钟视频验证全链路；旧 MineContext 页面全部正常。

## 8. 风险与缓释
- **大文件拖垮 worker**：上传前校验 + 后端限流，必要时把上传落入对象存储。
- **Markdown 注入**：严格白名单 + CSP。
- **并发编辑冲突**：暂不支持多人协作，后端返回 `updated_at`，前端保存时检测冲突并提示。
- **依赖膨胀**：React 项目只允许必要依赖（React、Zustand、remark/rehype、axios/fetch helper），禁止引入 UI 大杂烩。

## 9. 时间与里程碑（估算）
- 后端接口 & 数据模型：3 天。
- React 基础框架 + 上传/状态机：3 天。
- Markdown 编辑与预览：2 天。
- 高光/视觉卡组件 + 美术打磨：2 天。
- 测试（单元 + Playwright）& 验收：2 天。
- 总计：约 12 个工作日，可一后端一前端并行。

## 10. 开发准则
- 函数不得超过 120 行，嵌套不超过 3 层。
- React 组件无副作用，所有异步统一在 hooks/service 中处理。
- 配置默认关闭 Glass React UI，迁移完毕再切换默认值。
- 所有新接口写 `pytest` 与 `tests/glass/webui` 集成用例，覆盖 80% 以上。

> 做不到这些，别提上线。做到这些，Glass 才算有面子面对真实用户。
