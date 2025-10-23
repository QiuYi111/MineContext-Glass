# Glass 消费层与 CLI API Reference

本文档总结 MineContext Glass Phase 4 引入的消费层与辅助 CLI 接口，便于快速对接视频时间线产出的上下文。

## 1. Glass Context Source

模块：`glass.consumption.context_source`

### 1.1 `GlassContextSource`

```python
from glass.consumption import GlassContextSource, Modality

source = GlassContextSource()
items = source.get_items("timeline-20251029T010203Z")
contexts = source.get_processed_contexts("timeline-20251029T010203Z", modalities=[Modality.AUDIO])
strings = source.get_context_strings("timeline-20251029T010203Z")
grouped = source.group_by_context_type("timeline-20251029T010203Z")
```

关键行为：
- 自动调用 `GlassContextRepository.load_envelope()`，并根据 `segment_end` / `segment_start` 逆序排列上下文，确保最近片段优先。
- 支持 `modalities` 过滤，传入 `Sequence[Modality]` 即可筛选音频、帧等不同模态。
- `group_by_context_type()` 返回 `{context_type: list[ProcessedContext]}` 结构，直接喂给消费管理器。

## 2. 仓储扩展

模块：`glass.storage.context_repository`

### 2.1 `GlassContextRepository.upsert_aligned_segments(items)`

- 追加写入字段 `context_type`，捕捉 `ProcessedContext.extracted_data.context_type`。
- 入库 SQL 改为 `INSERT ... ON CONFLICT(context_id) DO UPDATE`，所有字段保持幂等。

### 2.2 `GlassContextRepository.load_envelope(timeline_id, modalities=None)`

```python
from glass.storage import GlassContextRepository

repo = GlassContextRepository()
envelope = repo.load_envelope("timeline-20251029T010203Z")
if envelope:
    for item in envelope.items:
        ...
```

- 读取 `glass_multimodal_context`（包含新增 `context_type` 列），复原 `ProcessedContext`，并打包成 `ContextEnvelope`。
- 为缺失或不可识别的模态/上下文进行日志过滤，保证消费层拿到的是一致且有效的条目。

## 3. 消费器适配

以下模块新增 `timeline_id` 参数，并在存在该参数时优先消费 Glass 时间线，同时保留原有数据路径：

| 模块 | 位置 | 备注 |
| --- | --- | --- |
| `ReportGenerator.generate_report()` | `opencontext/context_consumption/generation/generation_report.py` | timeline 上下文优先走 `_get_timeline_context_strings()`，未命中时落回全局查询。 |
| `RealtimeActivityMonitor.generate_realtime_activity_summary()` | `opencontext/context_consumption/generation/realtime_activity_monitor.py` | `group_by_context_type()` 输出并按时间线排序，fallback 原过滤。 |
| `SmartTipGenerator.generate_smart_tip()` | `opencontext/context_consumption/generation/smart_tip_generator.py` | `_get_comprehensive_contexts()` 支持 timeline。 |
| `SmartTodoManager.generate_todo_tasks()` | `opencontext/context_consumption/generation/smart_todo_manager.py` | `_get_task_relevant_contexts()` 支持 timeline。 |

`ConsumptionManager.generate_report()` 支持 `timeline_id` 透传，并新增 `_await_coroutine()`，确保在同步上下文中安全等待异步生成器。

## 4. CLI 扩展

命令：`opencontext glass report`

```bash
uv run opencontext glass report \
  --config config/config.yaml \
  --timeline-id timeline-20251029T010203Z \
  --lookback-minutes 90 \
  --output report.md
```

参数说明：
- `--timeline-id` (必选)：Glass ingestion 产出的时间线标识。
- `--start` / `--end`：ISO8601 或 Unix 秒级时间戳。若缺省则使用 `--lookback-minutes` 计算窗口。
- `--lookback-minutes`：未提供 `start` / `end` 时的回溯窗口（默认 60 分钟）。
- `--output`：可选文件路径，写入生成的 Markdown 报告；未指定时直接打印到标准输出。

内部流程：
1. `_resolve_report_window()` 解析时间窗口。
2. `_ensure_storage_initialized()` 校验存储准备完毕。
3. `ReportGenerator.generate_report()` 聚焦指定 timeline，结果持久化后返回。

## 5. 调试接口

`opencontext/server/routes/debug.py` 新增 `timeline_id` 查询参数：

- `POST /api/debug/generate/report`
- `POST /api/debug/generate/activity`
- `POST /api/debug/generate/tips`
- `POST /api/debug/generate/todos`
- `POST /api/debug/generate/{category}/custom`

调用示例：

```bash
curl -X POST "http://localhost:8000/api/debug/generate/report?timeline_id=timeline-20251029T010203Z"
```

消费链路因此可以在无需修改现有 API 的情况下，按需聚焦单个 Glass 时间线，验证不同模块的输出。
