# VideoManager API Reference

本文档描述 MineContext Glass 视频输入层的核心接口，帮助开发者在不破坏原有 MineContext 管线的前提下扩展或重用视频处理能力。

## 核心抽象：`VideoManager`

路径：`glass/ingestion/video_manager.py`

```python
class VideoManager(ABC):
    def ingest(self, source: Path | str, *, timeline_id: Optional[str] = None) -> AlignmentManifest: ...
    def get_status(self, timeline_id: str) -> IngestionStatus: ...
    def fetch_manifest(self, timeline_id: str) -> AlignmentManifest: ...
```

- `ingest`: 触发视频抽帧、音频抽取与转写流程。若传入 `timeline_id`，必须保证幂等；否则实现应生成稳定的唯一 ID。返回值是标准化的 `AlignmentManifest`。
- `get_status`: 查询时间线的处理状态，返回 `IngestionStatus`（`pending | processing | completed | failed`）。
- `fetch_manifest`: 读取已存在的 manifest；如果时间线不存在，抛出 `TimelineNotFoundError`。

## 标准实现：`LocalVideoManager`

路径：`glass/ingestion/local_video_manager.py`

```python
speech_runner = AUCTurboRunner(AUCTurboConfig(app_key="...", access_key="..."))
manager = LocalVideoManager(
    base_dir=Path("persist/glass"),
    frame_rate=1.0,
    ffmpeg_runner=FFmpegRunner(),
    speech_runner=speech_runner,
)
manifest = manager.ingest("videos/sample.mp4")
```

- 所有产物落在 `base_dir/<timeline_id>/`，默认目录为 `persist/glass`。
- 关键输出：
  - `alignment_manifest.json`
  - `status.json`
  - `transcription_raw.json`
  - `frames/`、`audio.wav`
- 抽帧频率通过 `frame_rate` 控制；必须大于 0。

### 错误处理
- 输入文件不存在 → `FileNotFoundError`
- 火山极速识别 / ffmpeg 异常 → 捕获并将状态写为 `failed`，然后重新抛出原始异常。
- 读取未知时间线 → `TimelineNotFoundError`

## 数据模型

路径：`glass/ingestion/models.py`

```python
class AlignmentSegment(BaseModel):
    start: float
    end: float
    type: SegmentType  # audio | frame | metadata
    payload: str
```

```python
class AlignmentManifest(BaseModel):
    timeline_id: str
    source: str
    segments: list[AlignmentSegment]
```

约束：
- `end >= start`，否则抛出 `ValueError`。
- `segments` 不可为空，自动按照 `start` 排序。
- `iter_segments(segment_type=...)` 可按模态过滤。
- `to_json()` 以稳定格式导出。

## 依赖组件

### `FFmpegRunner`
- 入口：`glass/ingestion/ffmpeg_runner.py`
- 方法：
  - `extract_frames(video_path, fps, output_dir, image_pattern="frame_%05d.png")`
  - `extract_audio(video_path, output_path)`
  - `cleanup(paths)`
- 默认使用系统 `ffmpeg`；可通过构造参数覆盖。

### `AUCTurboRunner`
- 入口：`glass/ingestion/auc_runner.py`
- 配置：`AUCTurboConfig`（`base_url`、`resource_id`、`app_key`、`access_key`、`model_name` 等）。
- 方法：
  - `transcribe(audio_path, timeline_id=...)`：将音频发送到火山极速识别并返回 `TranscriptionResult`。
  - 错误时抛出 `AUCTurboError`，并带上 `request_id` 方便定位问题。

## 典型工作流
1. 通过 `LocalVideoManager.ingest()` 处理原始视频。
2. 使用 `AlignmentManifest.iter_segments()` 遍历帧与音频片段。
3. 将 manifest 传递给后续的处理层（chunkers、embedding manager）。
4. 通过 `get_status`/`fetch_manifest` 对接前端任务进度或重试逻辑。

## 测试
- 单元测试：`glass/tests/ingestion/test_video_manager.py`
- 端到端测试：`glass/tests/ingestion/test_local_video_manager_integration.py`（需 `videos/22-10/Video Playback.mp4`）
- 命令：`uv run pytest glass/tests/ingestion -q`

## 扩展建议
- 如需接入分布式/远程处理，可继承 `VideoManager` 并替换 `LocalVideoManager`，保持 manifest 与状态接口一致。
- 引入额外模态（如 OCR、传感器数据）时，扩展 `SegmentType` 并保证 `AlignmentSegment` 仍由 `VideoManager` 统一生成，禁止在下游新增 if/else。
