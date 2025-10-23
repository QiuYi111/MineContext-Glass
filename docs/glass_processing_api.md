# Glass Processing API Reference

本页记录 MineContext Glass Phase 3 引入的处理层接口，方便后续阶段复用与扩展。所有模块默认位于 `glass.processing` 命名空间，并尽量重用 MineContext 现有的数据模型（参阅 `docs/reuse_reference.md`）。

## 1. ManifestChunker (`glass.processing.chunkers`)

```python
from glass.processing.chunkers import ManifestChunker, build_context_items
```

### 关键职责
- 接受 `AlignmentManifest`，输出 `MultimodalContextItem` 列表。
- 通过 `_build_audio_items()` 将音频段落转为 `ProcessedContext`（文本 chunk），复用 `SimpleTextChunker`。
- 通过 `_build_frame_item()` 将帧段落转为 `ProcessedContext`（图片上下文），附带时间轴元数据。

### 重要方法
| 方法 | 描述 |
| --- | --- |
| `ManifestChunker(clock=None, text_chunker=None)` | 可选注入时钟或文本 chunker，方便测试。 |
| `build_items(manifest)` | 产出 `list[MultimodalContextItem]`，每项包含 timeline 元数据与模态类型。 |
| `build_context_items(manifest)` | 无状态辅助函数，直接返回 `ManifestChunker().build_items(...)`。 |

### 输出元数据
- `context.metadata` 中统一包含 `timeline_id`、`segment_start`、`segment_end`、`segment_type`、`source_video`。
- `MultimodalContextItem` 上同步写入 `timeline_id`、`modality`、`content_ref`，便于下游检索。

## 2. GlassTimelineProcessor (`glass.processing.timeline_processor`)

```python
from glass.processing.timeline_processor import GlassTimelineProcessor
```

### 关键职责
- 实现 `BaseContextProcessor` 接口，处理带 `timeline_id` 的 `RawContextProperties`。
- 装载 manifest（文件路径或内联 JSON），调用 `ManifestChunker` 生成上下文条目。
- 将结果持久化：向量数据通过 `GlassContextRepository.upsert_aligned_segments()` 落库。
- 调用可选回调、维护统计信息，并缓存最近一次生成的 `ContextEnvelope`。

### 构造参数
- `repository`: 自定义 `GlassContextRepository`（默认自动解析全局存储）。
- `chunker`: 自定义 `ManifestChunker`（默认新建）。
- `visual_encoder`: 自定义视觉编码器；会对帧片段尝试向量化。

### 主要方法
| 方法 | 描述 |
| --- | --- |
| `can_process(raw_context)` | 检查 `timeline_id`、`ContextSource.VIDEO`、manifest 路径是否齐备。 |
| `process(raw_context)` | 返回 `list[ProcessedContext]`，并写入数据库。 |
| `shutdown(graceful=False)` | 轻量钩子，当前无额外资源需释放。 |
| `last_envelope` | 最近一次生成的 `ContextEnvelope` 缓存。 |

## 3. ContextEnvelope (`glass.processing.envelope`)

```python
from glass.processing.envelope import ContextEnvelope
```

### 用途
- 为消费层提供 timeline 级聚合结构：`timeline_id`、`source`、`items[list[MultimodalContextItem]]`。
- `from_items()` 可直接由 `GlassTimelineProcessor` 构造，保持与 manifest 对齐。

## 4. VisualEncoder (`glass.processing.visual_encoder`)

```python
from glass.processing.visual_encoder import VisualEncoder
```

### 关键职责
- 对帧图片执行最佳努力的向量化，复用全局 `global_embedding_client`。
- 若嵌入服务未初始化或调用失败，会记录日志并返回原始 `Vectorize` 对象，避免硬失败。

### 接口
| 方法 | 描述 |
| --- | --- |
| `encode(image_path)` | 返回 `Vectorize`（带 `ContentFormat.IMAGE`），成功时填充 `vector`。 |

## 5. 配置与启用

`config/config.yaml`：

```yaml
processing:
  glass_timeline_processor:
    enabled: true
```

- 设置为 `true` 后，`ComponentInitializer` 会注册 `glass_timeline_processor`，`ContextProcessorManager` 会自动把带 `timeline_id` 的输入路由给它。
- 若需要完全禁用，只需将 `enabled` 改为 `false`；老的 MineContext 截屏、文档处理链路不受影响。

## 6. 测试

- 单元测试位于 `glass/tests/processing/test_manifest_processing.py`，覆盖 chunker 输出、持久化写入、视觉编码标记。
- 推荐命令：
  ```bash
  UV_CACHE_DIR="$(pwd)/.uv-cache" uv run pytest glass/tests/processing -q
  ```
