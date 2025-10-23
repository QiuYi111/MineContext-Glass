# Glass 数据层 API Reference

本节说明 MineContext Glass Phase 2 引入的核心数据层组件，帮助在保持 MineContext 兼容的前提下接入多模态时间线数据。

## 数据模型

### `Modality`
逐字枚举当前支持的模态类型，所有值均为字符串。

| 值 | 说明 |
| --- | --- |
| `audio` | 音频转写片段 |
| `frame` | 视频关键帧 |
| `metadata` | 额外的时间线辅助信息（如场景标签） |
| `text` | 额外补录的纯文本片段 |

### `MultimodalContextItem`
`glass/storage/models.py`

| 字段 | 类型 | 描述 |
| --- | --- | --- |
| `context` | `ProcessedContext` | MineContext 现有上下文实体，保持统一向量化流程。 |
| `timeline_id` | `str` | 时间线标识，来源于 Phase 1 的 `AlignmentManifest`。 |
| `modality` | `Modality` | 模态类型，决定后续消费策略。 |
| `content_ref` | `str` | 指向原始资源（帧文件名、转写文本等）。 |
| `embedding_ready` | `bool` | 表示该条上下文是否已经完成向量化入库。 |

> 设计原则：将全部补充元数据绑定在 `ProcessedContext` 之外，避免改动原有数据模型。

## 仓储入口

### `GlassContextRepository`
`glass/storage/context_repository.py`

统一处理向量存储与 SQLite 元数据持久化。

#### 初始化
```python
from glass.storage import GlassContextRepository

repo = GlassContextRepository()  # 自动获取已初始化的 UnifiedStorage 与 SQLite 连接
```

可选参数：
- `storage`: 传入自定义 `UnifiedStorage`，便于测试或离线环境。
- `connection`: 传入自定义 `sqlite3.Connection`。若省略则从默认文档库中提取。

#### `upsert_aligned_segments(items: Sequence[MultimodalContextItem]) -> list[str]`
- 批量写入向量库（通过 `UnifiedStorage.batch_upsert_processed_context`）；
- 将模态元数据写入 SQLite 的 `glass_multimodal_context`；
- 返回最终写入的 `context_id` 列表；
- 若向量后端返回 ID 数量与输入不符，抛出 `ValueError`。

事务语义：任一阶段异常都会触发 SQLite 回滚，向量入库由后端保证幂等。

#### `fetch_by_timeline(timeline_id: str) -> list[sqlite3.Row]`
调试/验证辅助接口。按 `timeline_id` 读取 `glass_multimodal_context` 原始行，默认按 `context_id` 排序。

## SQLite Schema

表：`glass_multimodal_context`

| 列名 | 类型 | 约束 | 描述 |
| --- | --- | --- | --- |
| `id` | INTEGER | 主键 | 自增标识 |
| `timeline_id` | TEXT | NOT NULL | 时间线标识 |
| `context_id` | TEXT | NOT NULL UNIQUE | 对应 `ProcessedContext.id` |
| `modality` | TEXT | NOT NULL | 对应 `Modality` 枚举 |
| `content_ref` | TEXT | NOT NULL | 原始资源引用 |
| `embedding_ready` | BOOLEAN | DEFAULT 0 | 向量化是否完成 |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

索引：
- `idx_glass_multimodal_timeline`：加速 `timeline_id` 查询；
- `idx_glass_multimodal_context_id`：确保 `context_id` 唯一查找。

## 示例：写入对齐片段

```python
from glass.storage import GlassContextRepository, Modality, MultimodalContextItem
from opencontext.models.context import ProcessedContext

repo = GlassContextRepository()
context = ...  # 已构造好的 ProcessedContext

item = MultimodalContextItem(
    context=context,
    timeline_id="timeline-20251024T120000Z",
    modality=Modality.AUDIO,
    content_ref="segments/clip_0001.json",
    embedding_ready=True,
)

repo.upsert_aligned_segments([item])
```

执行成功后：
- 向量库会新增/更新对应 `ProcessedContext`；
- SQLite 表 `glass_multimodal_context` 记录时间线与模态元数据，下游消费层可直接按 `timeline_id` 拉取。
