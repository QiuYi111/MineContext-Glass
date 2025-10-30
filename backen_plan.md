# Glass WebUI 后端整备计划（Linus 版）

## 0. 前提与铁律

- 这是个真问题：当前 FastAPI 只是吐 demo JSON，与 CLI 产出的 manifest、report 完全脱节。
- 更简单的方法：直接复用仓库里现成的 `GlassIngestionService` + `DailyReportService`，别再造假流水线。
- Never break userspace：对外仍然暴露 `/glass/*` 这一套 schema，任何字段兼容 `glass start` 真实输出。

## 1. 现状快照

- 接口层：`glass/webui/backend/app.py` 一把梭，直接在 handler 内改状态。
- 数据结构：`TimelineRepository` 是进程内 dict，`TimelineRecord` 自己拼 Markdown。
- 服务层：`IngestionCoordinator._process_pipeline` 只是 `sleep` 加模板字符串。
- 与真实流水线的差距：没有 `GlassIngestionService`、`GlassContextRepository`、`DailyReportService` 的参与，重启即丢全量状态。

## 2. Linus 五层审视

### 2.1 数据结构

- 核心对象应该是：
  - 上传任务：包含 `timeline_id`、文件路径、状态、错误、触发时间。
  - 多模态上下文：沿用 `glass.storage.GlassContextRepository` 里 SQLite + 向量存储。
  - 日报：复用 `glass.storage.DailyReportRecord` + `glass.reports.models.DailyReport`。
- 关系：
  1. 上传记录驱动 `GlassIngestionService` 去产出 manifest。
  2. manifest 进入 `ContextProcessorManager` → 写入 `GlassContextRepository`。
  3. `DailyReportService` 用刚写进来的 envelope 生成 Markdown。
- 现状的问题：自行维护的 `TimelineRecord` 与真实上下文无关，导致所有下游结构都是假货。

### 2.2 特殊情况识别

- `get_report` 里强行把未完成任务标记为完成，这是典型的“为 demo 勉强贴创可贴”。
- Demo/Real 共用假造字段，切换模式必定 break。
- 上传命名冲突靠前缀数字堆叠，缺乏 timeline 级别的状态机持久化；失败、重试都没有分支。
- 清理方式：引入真正的状态表 + Pipeline 输出，特殊情况自然消失。

### 2.3 复杂度审查

- 功能本质：包装现有 CLI 的 ingestion→processing→report 链路成一组 REST API。
- 当前代码引入了一堆 `DailyReportBuilder` 等假构造器，把核心逻辑藏在 demo 模块里，除了让人误会什么都没解决。
- 简化路线：FastAPI handler 只做参数解析和调用 service；状态机集中在 `services` 层，但全部基于真实组件。

### 2.4 破坏性分析

- 现有前端依赖字段：`/glass/status`、`/glass/report`、`/glass/context`。改造时必须维持字段命名、类型不变。
- CLI 用户使用 `glass start` 产出的 sqlite/embeddings，后端要读取同一目录，不能破坏原有数据布局。
- Demo 模式仍需存在，但要从真实流水线导出的快照里读数据，不能再造 schema。

### 2.5 实用性验证

- 真实痛点：团队需要一个可用 WebUI 去消费 `glass start` 的结果；现在后端不能用，线上根本跑不起来。
- 目标方案复杂度：复用已有服务，额外写的就是状态表 + API glue，和痛点严重度匹配。

## 3. 目标态

- 后端内核替换为：
  - 上传：`GlassIngestionService`（线程池执行 ingestion + processor）。
  - Context/Report：`GlassContextRepository` + `DailyReportService`。
  - 状态持久化：最笨的 sqlite 表（或 jsonl）记录 `upload_tasks`，FastAPI 重启可恢复。
- API 契约保持 `/glass/upload|status|context|report` 四条线不变，`generate` 触发真正的重跑。
- Demo 模式：开机即加载真实快照（同 schema），接口逻辑与真实模式一致，只是数据源换成快照。

## 4. 分阶段落地

### 阶段 1：替换后端核心服务（不动 API）


# Glass WebUI Backend 整备进展（阶段 1）

## 今日完成

- 建立 SQLite `UploadTaskRepository`，持久化 `timeline_id`、状态、错误与时间戳，保证 FastAPI 重启后的任务可恢复。
- FastAPI `create_app` 接入真实的 `GlassIngestionService`、`GlassContextRepository` 与 `DailyReportService`，移除 demo-only 处理链。
- `IngestionCoordinator` 重写：提交任务直接调用线程池 ingestion，回写状态库，针对处理中请求返回 409，并提供 `build_context_payload` 映射真实 `ContextEnvelope` 到旧前端 schema。
- Demo 模式加载快照时同步写入状态库，保持 `/glass/*` 接口字段不变。

## 测试

- `uv run python -m pytest glass/webui/backend/tests/test_app.py`

1. 引入上传状态表（sqlite）：字段含 timeline_id、filename、source_path、status、error、submitted_at、completed_at。
2. 在 `create_app` 中实例化 `GlassIngestionService`、`DailyReportService`、`GlassContextRepository`。
3. `POST /glass/upload`：
   - 保存上传文件到 `GlassIngestionService.upload_dir`。
   - 将任务写入状态表，调用 `ingestion_service.submit`。
4. `GET /glass/status/{id}`：
   - 从状态表读取状态；若任务失败返回 error；若任务完成则确认 repos 中 envelope 存在。
5. 后台线程监听 `Future` 结果：成功→状态表标记 `processing/completed`；异常→写 `failed` + error。

### 阶段 2：接通日报与上下文接口

1. `GET /glass/context/{id}` 从 `GlassContextRepository.load_envelope` 拉真实数据，映射到旧 schema。
2. `GET /glass/report/{id}` 用 `DailyReportService.get_report`；若 envelope 未就绪返回 409/processing。
3. `PUT /glass/report/{id}` 调 `DailyReportService.save_manual_report`，并将结果写回。
4. `POST /glass/report/{id}/generate`：
   - 检查 timeline 是否存在；
   - 清理旧 manual 状态，重新提交给 `GlassIngestionService`（或调用新的再处理入口）。
5. 写契约测试：对比 CLI `glass start` 产出的 JSON 与 API 响应。

#### 阶段 2 进展（已完成部分）

- `IngestionCoordinator.build_context_payload` 直接读取 `GlassContextRepository` 的 envelope，并调用 `DailyReportService` 返回真实 `summary/highlights/visual_cards`，没有 envelope 就抛 409，demo 模式才回退 legacy。
- `get_daily_report`/`save_manual_report` 改为走 `DailyReportService`，用 `ReportNotReadyError` 统一映射到 409；手动报告保存成功后会把 Markdown/metadata 写回 SQLite。
- `regenerate_report` 在真实模式下清理 `GlassContextRepository.clear_daily_report`，保持旧 schema 不变但确保手动内容被丢弃，等待 pipeline 再次生成。
- FastAPI 层现在依赖注入真实的 `GlassIngestionService`、`GlassContextRepository`、`DailyReportService`，接口返回完全遵循 `/glass/*` 契约字段。
- 新增 pytest：`tests/test_ingestion_coordinator.py` 验证真实模式 envelope 提取、手动保存、再生成时手动状态被清空；`tests/test_app.py` 仍覆盖端到端上传/编辑路径。

### 阶段 3：Demo 模式与快照

1. 写脚本 `scripts/export_glass_snapshot.py`：从 sqlite 导出 envelope + report JSON。
2. Demo 模式读取快照生成只读状态表；API 与真实模式共用逻辑。
3. README + `.env` 指导：`GLASS_BACKEND_MODE=demo|real`；demo 不触发 ingestion。

### 阶段 4：运维与测试

1. 增加启动脚本：`uv run uvicorn glass.webui.backend.app:app --port 8765 --reload`。
2. pytest 覆盖：上传流程、失败回滚、report 契约、demo 快照加载。
3. 提供 smoke CLI：`scripts/seed_and_verify_backend.sh`（上传 -> 轮询 -> 校验 report）。
4. 前端协同：通知接口字段未变，仅状态语义变真实；更新轮询超时策略。

## 5. 技术要点与约束

- FastAPI 与线程池：`GlassIngestionService` 已经用 `ThreadPoolExecutor`，直接复用，避免 AsyncIO 嵌套写法失控。
- 配置：统一通过 `BackendConfig` 注入 ingest/upload 目录；新增字段 `storage_path` 指向 CLI 的 sqlite。
- 错误处理：失败的 Future 捕获异常 → 写 `upload_tasks.error`，`/glass/status` 返回 `failed` + message。
- 清理策略：上传文件 ingestion 成功后删除；失败保留以便排查，提供 `--preserve-failures` config。
- Never break userspace：手写序列化层，把 `DailyReport` 转回现有字段，必要时保留旧字段 `items`（空数组）以兼容前端。

## 6. 风险与应对

- **并发上传**：线程池默认 2 个 worker，状态表要加唯一索引，超出队列时返回 429。
- **上下文缺失**：pipeline 异常时 envelope 可能为空——直接报错，别再假装生成 Markdown。
- **Demo 数据老化**：在 release 前跑一次 CLI，重建快照；CI 可设 reminder。
- **存储权限**：确保 backend 运行账号对 `persist/` 有读写；文档里强调。

## 7. 验收标准

- 真实模式：上传测试视频 → `/glass/status` 先 pending/processing，再 completed → `/glass/report` 返回和 CLI 比对一致（字段逐个相等）。
- 失败路径：触发 ingestion 异常时 `/glass/status` 返回 `failed`，不生成 report。
- Demo 模式：启动后无需上传即可列出快照里的 timeline，report schema 与真实一致。
- 测试覆盖：新增 pytest 合集跑完；前端对接后可手动走完“上传→生成→编辑→重载”闭环。
