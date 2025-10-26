# MineContext Glass Implementation Plan — Linus Torvalds

## 0. 前置拷问（Linus 的三个问题）
- **这是个真问题还是臆想出来的？** 是真问题。我们已经有 MineContext 的纯赛博截屏版本，Glass 的第一视角视频数据才是更高带宽的真实上下文，需求已在业务场景里被验证。
- **有更简单的方法吗？** 有：在初期必须围绕现有 MineContext 管线复用，新增内容只限视频抽帧、转写与数据对齐层，避免另起炉灶。
- **会破坏什么吗？** 不允许破坏现有 MineContext 的 CLI、数据库 schema 与消费层协议。Glass 必须作为扩展路径接入，默认配置不改变旧用户体验。

## 1. 需求确认
我们要在 `glass/` 目录中落地一套 MineContext Glass 的实现计划，确保视频→上下文→LLM 消费的全链路可实作，同时维持原系统兼容性，并给 Codex 代理明确的执行路径。

## 2. 五层分析
### 2.1 数据结构
- **原子实体**：视频文件（多种编码）、音频转写结果（时间戳对齐文本）、关键帧（图像切片）、上下文片段（文本/视觉 embedding）、LLM 提示消费任务。
- **关系**：视频是时间轴，抽帧与转写都映射到统一的 `timeline_id`；上下文处理层消费 `timeline_id` 对齐后的 multimodal chunk；存储层需要一个统一的 `context_item` 抽象，包含 modality、时间范围、源引用。
- **流向**：输入层产出 aligned 原始上下文 → 处理层生成 embedding → 存储层（向量库 + 元数据）→ 消费层拉取。
- **所有权**：视频文件属于本地缓存，转写文本与帧特征存入数据库/对象存储；索引键必须由 `VideoManager` 分配并传递，避免多头生成。

### 2.2 特殊情况识别
- 视频格式差异、损坏帧、音频缺失、转写失败都是特殊情况。通过统一的导入流水线（ffmpeg 预处理 + AUC Turbo 转写）和状态机记录，将失败作为状态而非分支，避免在后续层级写 `if/else`。
- 多模态对齐需一次性完成，否则下游会遍地补丁。核心是生成 `alignment_manifest`，任何消费方只读 manifest。

### 2.3 复杂度审查
- 核心功能一句话：**把长视频变成结构化、可检索的上下文片段。**
- 必要概念：`VideoManager`、`alignment_manifest`、管线路由、前端上传器。坚持六个核心构件以内，其他通用逻辑复用 MineContext。
- 每个模块函数长度受控，按责任拆分：导入、对齐、入库、消费。

### 2.4 破坏性分析
- 不能影响现有 MineContext 截屏管线。所有新配置挂在 `config/glass.yaml`，CLI 新增 `opencontext glass ...`，默认不启用。
- 数据库 schema 仅追加表/字段，保持旧字段语义稳定。
- API 路由以 `/glass/*` 命名，不复用旧路径，避免用户脚本崩溃。

### 2.5 实用性验证
- 实际用户已经拍视频，需要自动化处理；手工转写/标注成本极高。我们提供的自动抽帧 + 对齐能立刻提升效率。
- 实现复杂度与价值匹配：新增的 heavy 逻辑集中在 `VideoManager` 和处理层适配，该投入与预期效果成正比。

## 3. 架构原则
- **好品味**：设计对齐后的数据模型，让视频/音频统一描述，避免后续每个模块加条件判断。
- **Never break userspace**：任何对现有 CLI、配置、数据库、API 的修改都加版本保护，默认关闭 Glass 模式。
- **实用主义**：优先选择成熟工具（ffmpeg、火山极速识别、sqlite/pg 向量扩展），不造轮子。
- **简洁执念**：模块最小化；拒绝超过三层嵌套的流程控制，所有异常用状态而非嵌套。

## 4. 实施路线图
### Phase 0：环境与目录基线
**状态：✅ 已完成（2025-10-23）**

**开发记录**
- 建立 `glass/` 子目录与对应的 `__init__.py`，同时编写 `glass/README.md` 说明模块边界。
- 更新 `pyproject.toml` 的打包列表，确保 `glass` 包随项目安装。
- 引入 `pytest.ini` 注册 `slow` 标记，方便区分长流程用例。

**验证**
- `uv run pytest glass/tests/ingestion -q`

### Phase 1：输入层（VideoManager）
**状态：✅ 已完成（2025-10-23）**

**开发记录**
- 定义 `VideoManager` 抽象与 `LocalVideoManager` 实现，落地 manifest 输出、状态文件与异常路径。
- 编写 `FFmpegRunner` 和 `AUCTurboRunner`，将抽帧、音频抽取、火山极速识别转写封装成可测单元。
- 建立 `AlignmentManifest` / `AlignmentSegment` 数据模型，自动排序并拒绝空段。
- 在 `persist/glass` 下输出 `alignment_manifest.json`、`status.json`、原始转写以支撑后续链路。

**验证**
- `uv run pytest glass/tests/ingestion -q`（含 `videos/22-10/Video Playback.mp4` 实例的端到端测试）

**产出规范**
- `alignment_manifest.json`：
   ```json
   {
     "timeline_id": "...",
     "source": "...",
     "segments": [
       {"start": 0.0, "end": 2.4, "type": "audio", "payload": "..."},
       {"start": 0.0, "end": 2.4, "type": "frame", "payload": "frame_0001.png"}
     ]
   }
   ```
- 单元与集成测试位于 `glass/tests/ingestion/`，其中 `test_local_video_manager_integration.py` 使用仓库示例视频验证真实路径。

### Phase 2：数据层扩展
**状态：✅ 已完成（2025-10-24）**

**开发记录**
- 在 `glass/storage/models.py` 定义 `Modality` 与 `MultimodalContextItem`，以 `ProcessedContext` 为核心消除额外 DTO。
- 更新 `opencontext/storage/backends/sqlite_backend.py`，追加 `glass_multimodal_context` 表及索引，纯新增列保持向后兼容。
- 新建 `glass/storage/context_repository.py`，封装向量双写与 SQLite 事务，`upsert_aligned_segments()` 保证一次提交。
- 编写 `glass/tests/storage/test_context_repository.py`，覆盖插入、幂等更新与异常回滚。

**验证**
- `uv run pytest glass/tests/storage -q`

### Phase 3：处理层适配

**状态：✅ 已完成（2025-10-26）**

**开发记录**
1. 在 `opencontext` 处理管线中增加 Glass 路由：`ContextProcessorManager` 检测 `timeline_id` 或 `ContextSource.VIDEO` 时转入 `glass_timeline_processor`，保持旧源类型逻辑不受影响。
2. 编写 `glass/processing/chunkers.py`，将 `AlignmentManifest` 转换为 MineContext 兼容的 `ProcessedContext`，消除多模态分支；文本复用 `SimpleTextChunker`，帧片段附带时间轴元数据。
3. 实现 `glass.processing.visual_encoder` 与 `GlassTimelineProcessor`，前者复用全局 embedding 客户端进行帧向量化，后者统一写入 `GlassContextRepository` 并生成 `ContextEnvelope`。
4. `processor_factory` 采用惰性注册，避免循环依赖；配置文件新增 `glass_timeline_processor` 开关并默认开启。

**验证**
- `pytest glass/tests/processing -q`
- 管线抽样运行 `uv run opencontext glass ingest ...`（手动验证）

### Phase 4：消费层整合
**状态：✅ 已完成（2025-10-29）**

**开发记录**
1. 新增 `glass.consumption.GlassContextSource`，封装 `GlassContextRepository.load_envelope()` 并按时间线片段逆序输出 `ProcessedContext`。
2. `GlassContextRepository` 追加 `context_type` 元数据写入与 `load_envelope()`，同时对 `glass_multimodal_context` schema 增列，兼容旧数据。
3. 报告 (`ReportGenerator`)、实时活动、提醒、待办等消费器接受可选 `timeline_id`，优先走 Glass 数据后再回落旧逻辑，排序统一使用 `segment_end` 元信息。
4. CLI 引入 `opencontext glass report` 命令，支持命令行生成时间线导向的日报并可落盘。
5. FastAPI 调试端点增加 `timeline_id` 查询参数，方便外部调试 Glass 上下文。

**验证**
- `UV_CACHE_DIR="$(pwd)/.uv-cache" uv run pytest glass/tests/storage glass/tests/consumption glass/tests/cli -q`
- 手动运行 `opencontext glass report --timeline-id <demo> --lookback-minutes 30`（需先完成 ingestion）确保 CLI 路径通畅。

### Phase 5：Web UI 与上传流程
1. `glass/ui/` 中搭建前端骨架（可先用现有 WebUI 框架）；提供拖拽上传、进度显示、任务刷新。
2. 后端新增 `/glass/upload`、`/glass/status/<timeline_id>`、`/glass/context/<timeline_id>` API。
3. 保持 UI 与 API 解耦：前端只识别 manifest 状态，不关心内部处理细节。
4. UI 交互测试和快照测试覆盖。

### Phase 6：部署与脚本
1. `scripts/install_glass.sh`：基于 `uv` 或 `mamba` 拉起环境，检测 CUDA。
2. Dockerfile 新增 `glass` 构建阶段，镜像中包含 ffmpeg 及访问火山极速识别所需的系统依赖（curl、ca 证书等）。
3. `build.sh` 扩展，允许 `./build.sh glass` 触发 PyInstaller + 资源打包。
4. 文档更新：`docs/glass_setup.md`、`README.md` 中加入 Glass 说明。

### 持续工作流
- 在 `glass/tests/` 中补足单元、集成和端到端测试。
- 加入 CI 任务：视频样本流水线 smoke test，确保“Never break userspace”。

## 5. 风险与缓释
- **依赖重量级库**：ffmpeg、音视频工具体积大 → 提前写安装脚本与缓存策略。
- **外部 API 可用性**：AUC Turbo 依赖公网访问和凭证配额 → 监控错误码，必要时提示稍后重试。
- **数据量膨胀**：关键帧与转写占用空间 → 设计清理策略（TTL、分级存储）。
- **隐私合规**：视频包含敏感信息 → 设计本地优先架构，禁默认上传云端。

## 6. 完成标准
- 从视频文件到 LLM 报告的全链路可在 `uv run opencontext glass ingest ...` + `opencontext glass report ...` 命令中跑通。
- 所有新模块具备 80%+ 测试覆盖率。
- 旧有 MineContext 功能在 CI 中全部通过，默认配置不启用 Glass 仍旧行为一致。
- 文档、脚本、示例完整，Codex 代理可以按步骤执行而不再提问。

## 7. 下一步执行提示
1. 实现 Phase 0/1，并在 `glass/tests` 中写基础测试，验证 manifest 结构。
2. 整合数据库适配层，保证 `Never break userspace`。
3. 逐步推进后续阶段，确保每阶段可独立验证。
