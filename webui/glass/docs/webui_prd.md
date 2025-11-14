# Glass WebUI PRD（Standalone 版）

## 0. 背景

- 前端 (`glass/webui`) 已能连接 `glass.webui.backend.app:app` 提供的轻量 FastAPI 服务，但该服务目前只写磁盘文件、生成假数据。  
- 当前实现（`services/ingestion.py`、`services/reports.py`）没有复用 CLI 中的真实 pipeline，`TimelineRepository` 也只是进程内存储，导致刷新即丢数据。  
- Demo 与 Real 模式共用一套假数据逻辑，和 `glass start` 输出的 manifest/markdown 不一致，实际接入后会 break userspace。

## 1. 问题评估

| 问题 | 描述 | 影响 |
| ---- | ---- | ---- |
| Pipeline 偏差 | `IngestionCoordinator._process_pipeline` 仅 `sleep` 后写入模板 Markdown，完全绕过 `glass` 包现有的 context capture → report 流程 | 产出的 `DailyReport`、`highlights`、`visual_cards` 与真实 CLI 不一致，前端联调或回归会失败 |
| 存储不可靠 | `TimelineRepository` 是进程内字典，`/glass/report/{id}` 返回值来自内存，服务重启后直接 404 | 无法承担最小可演示场景，也无法支撑前端刷新页面后的重载 |
| 状态机缺陷 | `get_report` 会强行把未完成任务改成 `COMPLETED` 并即时生成报告 | 和真实处理耗时、失败分支不符，前端无法正确反映处理进度或失败 |
| Demo 数据割裂 | `demo_data` 自己造 JSON，字段命名不遵循 CLI 现有模型 | Demo 模式产出的数据结构与真实流转不同，用户切换 real mode 时会遭遇 breakage |
| 前端触发逻辑缺席 | 文档描述 `GenerateAction`，但前端没有调用 `/glass/report/{id}/generate` 的真实实现 | 生成流程无法闭环，按钮行为缺失 |

## 2. 产品目标

1. 让 Standalone 后端严格复用 `glass start` 的视频→manifest→报告流水线，对外接口保持与现有 `/glass/*` 一致。  
2. 前端提供显式的上传与“Generate Daily Report”流程，状态反馈与 CLI 行为一致。  
3. Demo 模式用于演示 UI，但必须使用真实流水线产出的快照数据，确保契约一致。  
4. 提供一键开发、演示脚本，以及基础回归测试覆盖关键 API。

## 3. 功能需求

### 3.1 后端能力
- 使用 `glass.context_capture` 与 `glass.reports` 现有组件，实现上传后异步处理：  
  - `/glass/upload` 写入磁盘并把任务交给 pipeline，支持并发队列。  
  - `/glass/status/{id}` 暴露 `pending/processing/completed/failed`，状态从真实 pipeline 驱动。  
  - `/glass/report/{id}` 返回与 CLI 完全一致的 `DailyReport` 序列化，包括 `highlights`、`visual_cards`、`auto_markdown`。  
  - `/glass/report/{id}/generate` 触发重新跑 pipeline，而不是单纯重建模板。  
- 持久化层改为本地 sqlite/jsonl（最笨但可靠），支持重启恢复；需保存上传记录、生成结果、错误。  
- Demo 模式通过导出真实任务结果（`persist/` snapshot 或内置 json），加载时与真实模型保持同构。

### 3.2 前端能力
- 上传 → 轮询状态 → 点击 “Generate Daily Report” → 再轮询的串行流程，使用统一 API 封装，无额外特殊分支。  
- Demo/Real 模式通过 `.env` 或 CLI 变量切换同一 API schema。  
- 状态提示涵盖：上传进度、排队中、生成成功、生成失败（展示错误原因）。

### 3.3 运维与开发体验
- `uv run uvicorn ...` 启动后端，`npm run dev:real` 指向它，`npm run dev:demo` 加载内置 Demo 数据。  
- `./scripts/export_demo_payload.py` 从真实流水线输出 Demo 数据。  
- README 更新操作步骤、环境变量与故障排查。

## 4. 非功能 & 兼容性要求

- Never break userspace：REST schema、字段命名与 `glass` CLI 完全一致；必要时写契约测试对比 CLI JSON。  
- Pipeline 失败必须返回 `failed` 并附 `error` 字段，不能无声吞掉。  
- 处理延迟由真实 pipeline 决定，禁止在 API 层硬编码 `sleep`。  
- 代码复杂度控制：每个 handler 只做参数解析和调用服务，逻辑集中在可复用的 service 层。

## 5. 实施计划（建议 4 步）

| 阶段 | 目标 | 产出 |
| ---- | ---- | ---- |
| 1. Pipeline 接入 | 把 `IngestionCoordinator` 改为调用 `glass` pipeline，补上失败/日志/限流；引入持久化存储 | 可在命令行触发上传并生成真实报告 |
| 2. API 契约对齐 | 用 CLI 产出的 JSON 建契约测试，确保 `/glass/*` 响应与 CLI 一致；移除 `_process_pipeline` 内的假数据生成 | pytest + golden files |
| 3. 前端流程落地 | 实现 `GenerateAction`、状态轮询、错误反馈；完成 demo/real 模式切换逻辑 | 可在浏览器完成真实上传与生成 |
| 4. Demo 数据与文档 | 提取真实样例数据，编写 README、脚本，补充 Smoke/Playwright 测试 | 完整文档 + 演示脚本 |

## 6. 风险与对策

| 风险 | 对策 |
| ---- | ---- |
| Pipeline 接入复杂 | 优先用最笨方案：直接调用 CLI 同步流程，确认可行再异步化；保持函数签名简单 |
| 并发/持久化 bug | 使用 sqlite + 粗粒度锁，写集成测试覆盖上传冲突、重复生成 |
| Demo 数据老化 | 在 CI 中加脚本周期性刷新 demo json，或在发布前跑一次 CLI 快照 |
| 前后端契约漂移 | 增加 contract 测试：对同一视频运行 CLI 与服务，比对 JSON |

## 7. 验收标准

- 手动流程：上传一个测试视频 → 状态从 `processing` 切成 `completed` → 点击生成按钮返回 200 → `/glass/report/{id}` 与 CLI 输出一致。  
- 服务重启后仍能通过 `/glass/report/{id}` 取得历史报告。  
- Demo 模式页面展示的 `highlights`、`visual_cards` 字段与真实 schema 一致。  
- pytest 覆盖后端核心 service，Playwright（或最小 e2e）验证前端主流程。  
- README/脚本可指导新同学 10 分钟内完成运行。

## 8. 文档维护

- 本 PRD 与实现进度保持同步，重要变更需更新 `webui_prd.md`。  
- 关联的 CLI 对齐测试位置：`glass/webui/backend/tests/test_contract.py`（待补充）。

## 9. 最新进展（2024-xx-xx）

- 完成前端生成器 CTA：`glass/webui/src/components/GenerateAction.tsx`，新增“生成日报”按钮，依据时间线状态给提示文案。  
- App 集成逻辑：`glass/webui/src/App.tsx` 引入 `generateDailyReport` API，触发后将所选时间线状态重置为 `processing`，清空旧报告并重启轮询。  
- API 封装：`glass/webui/src/api.ts` 新增 `generateDailyReport(timelineId)`，封装 `/glass/report/:id/generate` 请求返回值。  
- 样式支持：`glass/webui/src/styles/generate-action.css` 定义 CTA 的玻璃拟态视觉与响应式布局。  
- 当前按钮仅调用现有轻量后端（仍为假数据流水线）；待 pipeline 接入真实 CLI 后，此 API 将直接触发重跑。  
