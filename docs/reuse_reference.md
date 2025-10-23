# OpenContext Component Reference for Reuse

This document summarizes the reusable parts of the OpenContext project for teams that want to embed its data model, processing pipeline, storage layer, and consumption services into a new application.

## 1. Pipeline Overview

```
Capture Components ──> RawContextProperties ──┐
                                              │
                                   ContextProcessorManager
                                              │
                                  ProcessedContext objects
                                              │
                                    UnifiedStorage backends
                                              │
                                 ConsumptionManager services
```

1. **Capture components** emit `RawContextProperties` instances (image, file, text sources).
2. **ContextProcessorManager** routes raw contexts to processors (document, screenshot, merger).
3. **Processors** transform raw data into `ProcessedContext` records, add vectors and metadata.
4. **UnifiedStorage** persists processed contexts in vector/document stores.
5. **ConsumptionManager** consumes processed data to produce reports, smart tips, todos, etc.

The sections below list API‑style details of each layer.

## 2. Data Models (`opencontext.models.context`)

All higher-level services rely on the Pydantic models defined here.

### 2.1 `Chunk`

Represents a chunked fragment from a raw document.

| Field | Type | Description |
| --- | --- | --- |
| `text` | `str | None` | Chunk text payload. |
| `image` | `bytes | None` | Optional image representation. |
| `chunk_index` | `int` | Position within the source. |
| `source_document_id` | `str | None` | Identifier of the source raw object. |
| `title`, `summary` | `str | None` | Human-friendly metadata. |
| `start_position`, `end_position`, `page_number` | `int | None` | Location metadata. |
| `section_path` | `list[str]` | Section breadcrumb path. |
| `referenced_images`, `referenced_tables` | `list[str]` | Linked resource IDs. |
| `semantic_type`, `importance_score`, `keywords`, `metadata` | Optional semantic annotations. |

### 2.2 `RawContextProperties`

Encapsulates captured raw data before processing.

| Field | Type | Description |
| --- | --- | --- |
| `content_format` | `ContentFormat` | Media type (TEXT, IMAGE, VIDEO). |
| `source` | `ContextSource` | Origin (SCREENSHOT, FILE, TEXT, etc.). |
| `create_time` | `datetime` | Timestamp of capture. |
| `object_id` | `str` | Unique capture identifier (auto UUID). |
| `content_path` | `str | None` | File path for non-text payloads. |
| `content_text` | `str | None` | Inline text payload. |
| `filter_path` | `str | None` | Optional filtering key. |
| `additional_info` | `dict | None` | Arbitrary metadata (e.g., window name). |
| `enable_merge` | `bool` | Signals merger participation. |

Methods:
- `to_dict() -> dict`
- `@classmethod from_dict(data: dict) -> RawContextProperties`

### 2.3 `ExtractedData`

Summarizes semantic information extracted from raw chunks.

| Field | Type |
| --- | --- |
| `title`, `summary` | `str | None` |
| `keywords`, `entities`, `tags` | `list[str]` |
| `context_type` | `ContextType` |
| `confidence`, `importance` | `int` |

### 2.4 `ContextProperties`

Links processed data back to original captures and tracking fields.

| Field | Type | Notes |
| --- | --- | --- |
| `raw_properties` | `list[RawContextProperties]` | One-to-many relationship. |
| `create_time`, `event_time`, `update_time` | `datetime` | Event chronology. |
| `duration_count`, `enable_merge` | `int`, `bool` | Merge heuristics. |
| `file_path`, `raw_type`, `raw_id` | `str | None` | Source tracking (vaults, files). |
| `call_count`, `merge_count`, `is_processed` | `int`, `bool` | Lifecycle counters. |

### 2.5 `Vectorize`

Describes content prepared for embedding.

- Fields: `content_format`, `image_path`, `text`, `vector`.
- `get_vectorize_content() -> str`: returns text or image path depending on format.

### 2.6 `ProcessedContext`

Primary storage object consumed by downstream services.

Fields:
- `id` (`str`): Defaults to UUID.
- `properties` (`ContextProperties`): Tracking container.
- `extracted_data` (`ExtractedData`): Semantic summary.
- `vectorize` (`Vectorize`): Embedding payload.
- `metadata` (`dict`): Additional structured info.

Methods:
- `get_vectorize_content() -> str`
- `get_llm_context_string() -> str`
- `to_dict() -> dict`
- `dump_json() -> str`
- `@classmethod from_dict(data: dict) -> ProcessedContext`

## 3. Processing Layer

### 3.1 Base Interfaces

#### `BaseContextProcessor` (`opencontext.context_processing.processor.base_processor`)

Abstract base class for processors.

Constructor:
```python
BaseContextProcessor(config: dict | None = None)
```

Key attributes:
- `config`: Effective configuration dict.
- `_processing_stats`: Counter dict.
- `_callback`: Optional downstream callback `[List[ProcessedContext]] -> None`.

Primary methods:
- `initialize(config: dict | None = None) -> bool`
- `validate_config(config: dict) -> bool`
- `can_process(context: Any) -> bool` (abstract)
- `process(context: Any) -> List[ProcessedContext]` (abstract)
- `batch_process(contexts: list[Any]) -> dict[str, list[ProcessedContext]]`
- `set_callback(callback: Callable[[List[ProcessedContext]], None])`
- `get_statistics() -> dict`
- `reset_statistics() -> bool`
- `shutdown(graceful: bool = False)` (optional override in subclasses)

Use this base class when authoring new processors for other data types.

### 3.2 `ContextProcessorManager` (`opencontext.managers.processor_manager`)

Coordinator that dispatches raw contexts to registered processors and optionally triggers a merger.

Constructor:
```python
ContextProcessorManager(max_workers: int = 5)
```

Important API:
- `register_processor(processor: IContextProcessor) -> bool`
- `set_merger(merger: IContextProcessor) -> None`
- `set_callback(callback: Callable[[List[Any]], None])`
- `process(initial_input: RawContextProperties) -> bool | List[ProcessedContext]`
- `batch_process(initial_inputs: list[RawContextProperties]) -> dict[str, list[ProcessedContext]]`
- `get_statistics() -> dict`
- `shutdown(graceful: bool = False) -> None`

Routing defaults (modifiable via `_define_routing()`):
- `ContextSource.SCREENSHOT` → `"screenshot_processor"`
- `ContextSource.FILE`, `ContextSource.TEXT`, `ContextSource.VAULT` → `"document_processor"`

### 3.3 Document Pipeline

#### `DocumentProcessor` (`opencontext.context_processing.processor.document_processor`)

Async processor for vault text and uploaded files. Uses an internal queue + worker thread.

Initialization:
```python
processor = DocumentProcessor()
processor.initialize()  # optional; config auto-loaded from GlobalConfig
```

Configuration keys (`processing.document_processor`):
- `batch_size` (default 10)
- `batch_timeout` seconds (default 5)
- `use_llm_chunker` (bool)

Key methods:
- `can_process(context: RawContextProperties) -> bool`
  - Accepts `ContextSource.TEXT` with inline text or file contexts with supported extensions.
- `process(context: RawContextProperties) -> bool`
  - Enqueues context for async handling.
- `shutdown(graceful: bool = False) -> None`

Internals:
- `_get_chunker()` picks `StructuredFileChunker`, `FAQChunker`, `SimpleTextChunker`, or `LLMDocumentChunker`.
- `_process_single_document()` transforms chunk list to `ProcessedContext` instances.
- Persists results through `get_storage().batch_upsert_processed_context`.

Integration tips:
- Always provide `additional_info` in `RawContextProperties` with `title`, `raw_id`, etc., so the processor can fill `ContextProperties`.
- Ensure `GlobalConfig` and storage are initialized before instantiating the processor in a standalone project.

### 3.4 Screenshot Pipeline

#### `ScreenshotProcessor` (`opencontext.context_processing.processor.screenshot_processor`)

Asynchronous screenshot analyzer using deduplication and VLMs.

Configuration keys (`processing.screenshot_processor`):
- `similarity_hash_threshold`
- `batch_size`, `batch_timeout`
- `max_image_size`, `resize_quality`
- `max_raw_properties`
- `enabled_delete` (delete duplicates on disk)

Public API:
- `can_process(context: RawContextProperties) -> bool`
- `process(context: RawContextProperties) -> bool`
- `shutdown(graceful: bool = False) -> None`

Behavior:
- Resizes incoming images, performs pHash deduplication (`_is_duplicate`).
- Buffers contexts until batch conditions are met, then runs `batch_process` async to call `generate_with_messages_async` (vision LLM) and `do_vectorize`.
- Persists generated `ProcessedContext` with `get_storage()`.

### 3.5 Processor Factory

`ProcessorFactory` (`opencontext.context_processing.processor.processor_factory`) centralizes processor creation:

```python
from opencontext.context_processing.processor.processor_factory import ProcessorFactory

factory = ProcessorFactory()
document_processor = factory.create_processor("document_processor")
```

- Built-in type names: `"document_processor"`, `"screenshot_processor"`, `"context_merger"`.
- Useful when wiring processors dynamically in a new service container.

## 4. Storage Layer

### 4.1 Interfaces (`opencontext.storage.base_storage`)

- `IVectorStorageBackend`: defines operations for vector DB (collections, upsert, search).
- `IDocumentStorageBackend`: CRUD utilities for vault/todo/report tables.
- `StorageType`, `DataType`, `StorageConfig`, `DocumentData`, `QueryResult`: shared enums and data classes.

Implement these interfaces to target alternative storage engines.

### 4.2 `UnifiedStorage` (`opencontext.storage.unified_storage`)

Central access point that instantiates backends from configuration.

Lifecycle:
```python
storage = UnifiedStorage()
storage.initialize()  # reads GlobalConfig storage.backends
storage.batch_upsert_processed_context(processed_contexts)
```

Key methods:
- `initialize() -> bool`
- `get_vector_collection_names() -> list[str] | None`
- `batch_upsert_processed_context(contexts: list[ProcessedContext]) -> list[str] | None`
- `upsert_processed_context(context: ProcessedContext) -> str | None`
- `get_all_processed_contexts(...) -> dict[str, list[ProcessedContext]]`
- `get_processed_context(id: str, context_type: str) -> ProcessedContext`
- `delete_processed_context(id: str, context_type: str) -> bool`
- `search(query: Vectorize, top_k=10, context_types=None, filters=None) -> list[tuple[ProcessedContext, float]]`
- Document DB passthroughs (`insert_vaults`, `get_vaults`, `update_vault`, etc.).

Backends shipped with the project:
- **Vector DB**: Chroma (local path configured under `persist/chromadb` by default).
- **Document DB**: SQLite (file configured under `persist/sqlite/app.db`).

### 4.3 `GlobalStorage` (`opencontext.storage.global_storage`)

Singleton wrapper that auto-loads configuration.

Usage:
```python
from opencontext.storage.global_storage import GlobalStorage, get_storage

global_storage = GlobalStorage.get_instance()
storage = get_storage()
storage.batch_upsert_processed_context(processed_contexts)
```

Provides convenience proxies (`upsert_processed_context`, `search_contexts`, etc.) and ensures only one `UnifiedStorage` is active.

When embedding in a new project:
1. Call `GlobalConfig.get_instance().initialize(config_path)` before retrieving storage.
2. Optionally replace backends by customizing `storage.backends` in your config YAML.

## 5. Consumption Layer

### 5.1 `ConsumptionManager` (`opencontext.managers.consumption_manager`)

Orchestrates scheduled generation tasks that consume `ProcessedContext` data.

Constructor:
```python
manager = ConsumptionManager()
```

Public API:
- `start_scheduled_tasks(config: dict | None = None) -> None`
  - Recognized keys: `daily_report_time`, `activity_interval`, `tips_interval`, `todos_interval`.
- `stop_scheduled_tasks() -> None`
- `shutdown() -> None`
- `get_statistics() -> dict`

Default generators instantiated:
- `ReportGenerator` (daily summaries)
- `RealtimeActivityMonitor`
- `SmartTipGenerator`
- `SmartTodoManager`

Each generator fetches data via `get_storage()` and publishes events through `EventManager`.

### 5.2 `EventManager` (`opencontext.managers.event_manager`)

Lightweight in-memory event cache.

API:
- `publish_event(event_type: EventType, data: dict) -> str`
- `fetch_and_clear_events() -> list[dict]`
- `get_cache_status() -> dict`

Use this to wire consumption outputs into custom notification channels.

## 6. Configuration Contracts (`config/config.yaml`)

Key sections relevant to reused components:

| Section | Purpose | Notable Keys |
| --- | --- | --- |
| `logging` | Set log level. | `level` |
| `capture.screenshot` | Interval, storage path for screenshots. | `capture_interval`, `storage_path`, `dedup_enabled` |
| `processing.document_processor` | Batch behavior, LLM chunker toggle. | `batch_size`, `batch_timeout`, `use_cloud_chunker` |
| `processing.screenshot_processor` | Dedup, batching, resizing. | `batch_size`, `max_image_size`, `enabled_delete` |
| `storage.backends` | Define vector/document backend configs. | `storage_type`, `backend`, `config.path` |
| `content_generation` | Control consumption manager scheduling. | `enabled`, `auto_start`, intervals |

When porting to a new project, provide a slimmed-down config that preserves these sections.

## 7. Integration Checklist for a New Project

1. **Install dependencies**: replicate requirements used by processing modules (Pydantic, FastAPI optional, PIL, mss, Chroma, SQLite, etc.).
2. **Copy source modules**:
   - `opencontext/models/context.py` and `opencontext/models/enums.py`
   - `opencontext/context_processing/**`
   - `opencontext/storage/**`
   - `opencontext/managers/processor_manager.py`, `consumption_manager.py`, `event_manager.py`
3. **Bring configuration utilities**:
   - `opencontext/config/global_config.py`
   - `opencontext/config/config_manager.py`
   - Default YAML (`config/config.yaml`) as a template.
4. **Initialize services**:
   ```python
   from opencontext.config.global_config import GlobalConfig
   from opencontext.storage.global_storage import GlobalStorage
   from opencontext.managers.processor_manager import ContextProcessorManager
   from opencontext.context_processing.processor.processor_factory import ProcessorFactory

   GlobalConfig.get_instance().initialize("config/config.yaml")
   GlobalStorage.get_instance()  # auto-initializes storage

   factory = ProcessorFactory()
   processor_manager = ContextProcessorManager()
   processor_manager.register_processor(factory.create_processor("document_processor"))
   processor_manager.register_processor(factory.create_processor("screenshot_processor"))
   ```
5. **Feed raw contexts**:
   ```python
   from opencontext.models.context import RawContextProperties, ContextSource, ContentFormat
   import datetime

   raw = RawContextProperties(
       source=ContextSource.TEXT,
       content_format=ContentFormat.TEXT,
       create_time=datetime.datetime.utcnow(),
       content_text="Example payload",
       additional_info={"title": "Sample"}
   )
   processor_manager.process(raw)
   ```
6. **Consume outputs**:
   - Read from `get_storage().get_all_processed_contexts(...)`.
   - Optionally start `ConsumptionManager` to generate reports or notifications.

7. **Shutdown gracefully**:
   ```python
   processor_manager.shutdown()
   ConsumptionManager().shutdown()
   ```

By following this reference, you can embed OpenContext's mature data pipeline into a new application while preserving the original project’s processing semantics and storage abstractions.
