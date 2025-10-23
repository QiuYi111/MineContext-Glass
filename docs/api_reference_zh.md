# OpenContext 可复用组件 API 参考（中文版）

本文档面向需要在新项目中复用 OpenContext 核心模块的团队，按照“数据模型 → 处理层 → 存储层 → 消费层”顺序介绍关键类、方法与集成要点。

---

## 1. 数据流总览

```
采集组件 ──> RawContextProperties ──┐
                                    │
                        ContextProcessorManager
                                    │
                         ProcessedContext 对象
                                    │
                           UnifiedStorage
                                    │
                         ConsumptionManager
```

1. 采集层将截图 / 文档 / 文本封装为 `RawContextProperties`。
2. 处理层根据来源分发给不同处理器，生成 `ProcessedContext`。
3. 存储层统一持久化向量与文档数据。
4. 消费层读取已处理上下文生成报告、提醒、待办等。

---

## 2. 数据模型（`opencontext/models/context.py`）

### 2.1 `Chunk`
描述文档拆分后的一段内容。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `text` | `str | None` | Chunk 文本内容 |
| `image` | `bytes | None` | 可选的图像数据 |
| `chunk_index` | `int` | 在原文档中的序号 |
| `source_document_id` | `str | None` | 对应原文档 ID |
| `title` / `summary` | `str | None` | 可选标题与摘要 |
| `start_position` / `end_position` | `int | None` | 文本起止位置 |
| `page_number` | `int | None` | 页码信息 |
| `section_path` | `list[str]` | 所属章节路径 |
| `referenced_images` / `referenced_tables` | `list[str]` | 引用的资源 ID |
| `semantic_type` / `importance_score` / `keywords` / `metadata` | 额外语义标注 |

### 2.2 `RawContextProperties`
封装采集获得的原始上下文。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `content_format` | `ContentFormat` | 媒体格式（TEXT、IMAGE、AUDIO…） |
| `source` | `ContextSource` | 来源（SCREENSHOT、FILE、TEXT…） |
| `create_time` | `datetime` | 采集时间 |
| `object_id` | `str` | 自动生成的唯一 ID |
| `content_path` | `str | None` | 非文本内容的文件路径 |
| `content_text` | `str | None` | 文本内容 |
| `filter_path` | `str | None` | 可选筛选路径 |
| `additional_info` | `dict | None` | 自定义元信息 |
| `enable_merge` | `bool` | 是否参与合并策略 |

常用方法：
- `to_dict() -> dict`
- `@classmethod from_dict(data: dict) -> RawContextProperties`

### 2.3 `ExtractedData`
承载处理后的语义摘要。

| 字段 | 类型 |
| --- | --- |
| `title` / `summary` | `str | None` |
| `keywords` / `entities` / `tags` | `list[str]` |
| `context_type` | `ContextType` |
| `confidence` / `importance` | `int` |

### 2.4 `ContextProperties`
连接处理结果与原始数据。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `raw_properties` | `list[RawContextProperties]` | 原始上下文引用 |
| `create_time` / `event_time` / `update_time` | `datetime` | 时间线 |
| `duration_count` | `int` | 上下文持续次数 |
| `enable_merge` | `bool` | 合并开关 |
| `file_path` / `raw_type` / `raw_id` | `str | None` | 追踪数据来源 |
| `call_count` / `merge_count` / `is_processed` 等 | 生命周期指标 |

### 2.5 `Vectorize`
描述向量化输入。

字段：`content_format`、`image_path`、`text`、`vector`。  
方法：`get_vectorize_content()` 返回适合向量化的文本或图像路径。

### 2.6 `ProcessedContext`
最终写入存储、供下游使用的结构化结果。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `str` | 默认 UUID |
| `properties` | `ContextProperties` | 生命周期与追踪信息 |
| `extracted_data` | `ExtractedData` | 语义摘要 |
| `vectorize` | `Vectorize` | 向量相关数据 |
| `metadata` | `dict` | 额外结构化信息 |

主要方法：
- `get_vectorize_content() -> str`
- `get_llm_context_string() -> str`：将标题、摘要、关键词、实体、上下文类型、metadata 以及时间信息拼接成多行文本，用于喂给大模型。
- `to_dict()` / `dump_json()` / `from_dict()` 等。

---

## 3. 处理层

### 3.1 抽象基类 `BaseContextProcessor`

位置：`opencontext/context_processing/processor/base_processor.py`

构造：
```python
BaseContextProcessor(config: dict | None = None)
```

核心属性：
- `config`：处理器配置（来自全局配置或构造参数）。
- `_processing_stats`：统计数据（处理次数、生成数量、错误数）。
- `_callback`：处理完成后回调函数 `Callable[[List[ProcessedContext]], None]`。

关键方法：
- `initialize(config: dict | None = None) -> bool`
- `validate_config(config: dict) -> bool`
- `can_process(context) -> bool`（抽象方法）
- `process(context) -> List[ProcessedContext]`（抽象方法）
- `batch_process(contexts: list) -> dict`
- `set_callback(callback)`
- `get_statistics() -> dict`
- `reset_statistics() -> bool`
- `shutdown(graceful: bool = False)`

> 继承此基类即可快速实现新的处理器。

### 3.2 `ContextProcessorManager`

位置：`opencontext/managers/processor_manager.py`

职责：注册处理器、路由 `RawContextProperties`、触发批量处理、管理合并器。

构造：
```python
ContextProcessorManager(max_workers: int = 5)
```

API：
- `register_processor(processor) -> bool`
- `set_merger(merger)`
- `set_callback(callback)`
- `process(initial_input: RawContextProperties) -> bool | list[ProcessedContext]`
- `batch_process(initial_inputs: list[RawContextProperties]) -> dict`
- `get_statistics() -> dict`
- `shutdown(graceful: bool = False)`

默认路由（可重写 `_define_routing()`）：
- `SCREENSHOT` → `"screenshot_processor"`
- `FILE` / `TEXT` / `VAULT` → `"document_processor"`

### 3.3 `DocumentProcessor`

位置：`opencontext/context_processing/processor/document_processor.py`

职责：异步处理文本和文件类原始上下文，按类型选择 chunker，生成 `ProcessedContext`。

配置项（`processing.document_processor`）：
- `batch_size`：队列批量大小（默认 10）
- `batch_timeout`：批处理超时（默认 5 秒）
- `use_llm_chunker`：是否启用 LLM chunker

关键点：
- `can_process()` 针对 `ContextSource.TEXT` 或 `ContextSource.FILE` 判断是否有合适 chunker。
- `_get_chunker()` 根据文件类型或扩展名选择 `StructuredFileChunker`、`FAQChunker`、`SimpleTextChunker` 或 `LLMDocumentChunker`。
- `_process_single_document()` 将 `RawContextProperties` 拆分成 `Chunk` 列表，再组装 `ProcessedContext`。
- 处理结果通过 `get_storage().batch_upsert_processed_context()` 落库。

### 3.4 `ScreenshotProcessor`

位置：`opencontext/context_processing/processor/screenshot_processor.py`

职责：异步处理截图，进行 pHash 去重、尺寸压缩、调用视觉大模型提取语义、生成向量化摘要。

配置项（`processing.screenshot_processor`）：
- `similarity_hash_threshold`
- `batch_size` / `batch_timeout`
- `max_image_size` / `resize_quality`
- `max_raw_properties`
- `enabled_delete`（是否删除重复截图文件）

流程：
1. `process()`：执行可选压缩与去重，将非重复截图放入队列。
2. `_run_processing_loop()`：批量取出截图，调用 `batch_process()`。
3. `batch_process()`：使用 Vision LLM、向量服务生成语义信息，再写入存储。

### 3.5 `ProcessorFactory`

位置：`opencontext/context_processing/processor/processor_factory.py`

用于按名称创建处理器：
```python
from opencontext.context_processing.processor.processor_factory import ProcessorFactory

factory = ProcessorFactory()
document_processor = factory.create_processor("document_processor")
```

内置类型：`document_processor`、`screenshot_processor`、`context_merger`。  
适用于在独立项目中动态装配处理器。

---

## 4. 存储层

### 4.1 接口定义（`opencontext/storage/base_storage.py`）

- `IVectorStorageBackend`：向量库接口，须实现集合管理、增删查向量、相似度搜索等。
- `IDocumentStorageBackend`：文档库接口（vault、报告、待办等）。
- 数据结构：`StorageType`、`DataType`、`StorageConfig`、`DocumentData`、`QueryResult`。

自定义存储后端时需实现上述接口。

### 4.2 `UnifiedStorage`

位置：`opencontext/storage/unified_storage.py`

功能：根据配置创建向量 / 文档后端，并提供统一操作入口。

基本用法：
```python
from opencontext.storage.unified_storage import UnifiedStorage

storage = UnifiedStorage()
storage.initialize()  # 自动读取 GlobalConfig 中的 storage.backends

storage.batch_upsert_processed_context(processed_contexts)
results = storage.get_all_processed_contexts(...)
```

关键方法：
- `initialize() -> bool`
- `get_vector_collection_names()`
- `batch_upsert_processed_context(contexts)`
- `upsert_processed_context(context)`
- `get_all_processed_contexts(context_types, limit, offset, filter, need_vector)`
- `get_processed_context(id, context_type)`
- `delete_processed_context(id, context_type)`
- `search(query: Vectorize, top_k, context_types, filters)`
- 文档存储相关：`insert_vaults`、`get_vaults`、`update_vault` 等。

默认后端：
- 向量库：Chroma（本地 `persist/chromadb`）。
- 文档库：SQLite（本地 `persist/sqlite/app.db`）。

### 4.3 `GlobalStorage`

位置：`opencontext/storage/global_storage.py`

作用：全局单例封装 `UnifiedStorage`，自动根据配置初始化（懒加载）。

常用方法：
```python
from opencontext.storage.global_storage import get_storage

storage = get_storage()
storage.batch_upsert_processed_context(processed_contexts)
```

还提供 `upsert_processed_context`、`search_contexts`、`get_context_types` 等便捷调用。

集成时需确保已调用：
```python
from opencontext.config.global_config import GlobalConfig

GlobalConfig.get_instance().initialize("config/config.yaml")
```

---

## 5. 消费层

### 5.1 `ConsumptionManager`

位置：`opencontext/managers/consumption_manager.py`

职责：调度报告、活动监测、灵感提示、智能待办等生成任务。

API：
- `start_scheduled_tasks(config: dict | None = None)`：可配置 `daily_report_time`、`activity_interval`、`tips_interval`、`todos_interval`。
- `stop_scheduled_tasks()`
- `shutdown()`
- `get_statistics()`

内部依赖的生成器：
- `ReportGenerator`
- `RealtimeActivityMonitor`
- `SmartTipGenerator`
- `SmartTodoManager`

这些生成器会从 `get_storage()` 中拉取 `ProcessedContext`，并通过 `EventManager` 发布事件。

### 5.2 `EventManager`

位置：`opencontext/managers/event_manager.py`

简单的事件缓存队列，用于消费模块对外输出。

API：
- `publish_event(event_type: EventType, data: dict) -> str`
- `fetch_and_clear_events() -> list[dict]`
- `get_cache_status() -> dict`

可将其与消息队列 / WebSocket 等结合，实现自定义通知。

---

## 6. 配置要点（`config/config.yaml`）

| 配置段 | 作用 | 重要键 |
| --- | --- | --- |
| `logging` | 日志等级 | `level` |
| `capture.screenshot` | 截图采集参数 | `capture_interval`、`storage_path`、`dedup_enabled` |
| `processing.document_processor` | 文档处理配置 | `batch_size`、`batch_timeout`、`use_cloud_chunker` |
| `processing.screenshot_processor` | 截图处理配置 | `batch_size`、`max_image_size`、`enabled_delete` |
| `storage.backends` | 向量与文档存储后端定义 | `storage_type`、`backend`、`config.path` |
| `content_generation` | 消费层调度 | `enabled`、`auto_start`、各类间隔 |

在新项目中应根据实际环境调整这些配置。

---

## 7. 集成步骤示例

1. **初始化配置与存储**
   ```python
   from opencontext.config.global_config import GlobalConfig
   from opencontext.storage.global_storage import GlobalStorage

   GlobalConfig.get_instance().initialize("config/config.yaml")
   GlobalStorage.get_instance()  # 懒加载 UnifiedStorage
   ```

2. **装配处理器**
   ```python
   from opencontext.context_processing.processor.processor_factory import ProcessorFactory
   from opencontext.managers.processor_manager import ContextProcessorManager

   factory = ProcessorFactory()
   processor_manager = ContextProcessorManager()
   processor_manager.register_processor(factory.create_processor("document_processor"))
   processor_manager.register_processor(factory.create_processor("screenshot_processor"))
   ```

3. **注入原始上下文**
   ```python
   import datetime
   from opencontext.models.context import RawContextProperties, ContextSource, ContentFormat

   raw = RawContextProperties(
       source=ContextSource.TEXT,
       content_format=ContentFormat.TEXT,
       create_time=datetime.datetime.utcnow(),
       content_text="示例文本",
       additional_info={"title": "示例标题"}
   )
   processor_manager.process(raw)
   ```

4. **读取已处理上下文 / 触发消费层**
   ```python
   storage = get_storage()
   contexts = storage.get_all_processed_contexts(limit=50)

   from opencontext.managers.consumption_manager import ConsumptionManager
   consumption_manager = ConsumptionManager()
   consumption_manager.start_scheduled_tasks()
   ```

5. **关闭组件**
   ```python
   processor_manager.shutdown()
   consumption_manager.shutdown()
   ```

---

通过以上 API 参考和示例，新项目可以快速继承 OpenContext 的成熟数据处理、存储与消费能力，并在此基础上扩展自定义的处理器、存储后端或消费方式。欢迎根据业务需求调整配置或丰富 `ContentFormat`、`ContextType`、生成器等枚举和模块。*** End Patch
