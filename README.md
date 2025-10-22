<div align="center">

<picture>
  <img alt="MineContext" src="src/MineContext-Banner.svg" width="100%" height="auto">
</picture>

### MineContext Glass: Full-Spectrum Personal Context OS

Built on ByteDance's [MineContext](https://github.com/volcengine/MineContext), extending the original open-source project into a glasses-first personal context platform.

</div>

## Table of Contents

- [Vision](#vision)
- [Current Capabilities](#current-capabilities)
- [Roadmap](#roadmap)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Start the Pipeline](#start-the-pipeline)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [License](#license)

## Vision

MineContext Glass reimagines personal context management around daily life. Using smart glasses, we capture day-long video streams and transform them into an organized, searchable knowledge base that bridges the physical and digital worlds. Every clip becomes part of a living memory system that powers summaries, reminders, and intelligent recommendations.

By standing on MineContext's mature context engineering foundations, we combine the existing cyberspace context (screen captures, documents, chats) with real-life visuals to create a full-spectrum, proactive assistant. The next milestone is speech recognition extracted from captured video audio, so conversations and spoken cues join the same context graph.

## Current Capabilities

- Continuous video ingestion from supported smart glasses, including automatic transfer, transcoding, and secure local storage.
- Adaptive frame sampling and embedding generation to distill long recordings into meaningful context snippets ready for retrieval.
- Unified context indexing that merges video-derived insights with the original MineContext knowledge base.
- Event and highlight surfacing that transforms raw clips into timelines, daily digests, and recall prompts.

## Roadmap

| Status           | Milestone              | Description                                                                        |
| ---------------- | ---------------------- | ---------------------------------------------------------------------------------- |
| ✅ Completed     | Video capture pipeline | Daily video recording, compression, and context extraction are production-ready.   |
| 🛠️ In Progress | Speech recognition     | Transcribe on-device audio to bring voice context into the knowledge graph.        |
| 🧪 Planned       | Multimodal synthesis   | Fuse visual, audio, and digital signals into richer summaries and proactive tasks. |

## Quick Start

This repository keeps MineContext's developer tooling while adding the video processing stack.

### Prerequisites

- macOS or Linux with Python 3.9+.
- `uv` package manager (recommended) or a Python virtual environment.
- Optional: connected smart glasses with USB or Wi‑Fi file sync.

### Installation

```bash
uv sync
```

Or use a traditional virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Configuration

1. Duplicate `config/config.yaml.example` (or your existing MineContext config) to `config/config.yaml`.
2. Set API keys, embedding models, and storage paths as needed.
3. Under the new `[video]` section, configure the glasses import directory and transcoding preferences.

### Start the Pipeline

Run the context server with:

```bash
uv run opencontext start --port 8000 --config config/config.yaml
```

Glasses footage dropped into the configured import path will be processed automatically. Use the CLI or API endpoints to inspect timelines, digests, and retrieved clips.

### Daily Vlog Ingest

For scheduled processing of a day's recordings, place raw `.mp4` files under `videos/<DATE>/` (for example `videos/2025-02-27/12-13.mp4`) and run:

```bash
uv run opencontext.tools.daily_vlog_ingest
```

The tool extracts frames, updates the context store, and writes summaries to `persist/reports/<date>.md`. Adjust the target date or frame interval with flags such as `--date YYYY-MM-DD` and `--frame-interval 5`.

## Architecture

MineContext Glass keeps the original context-flow of `context_capture → context_processing → storage → server routes`, expanding the capture stage with a dedicated video manager.

- **Video Capture Manager** (upcoming) pulls footage from smart glasses, handles deduplication, and writes raw assets to managed storage.
- **Video Processing Pipeline** extracts frames, runs embeddings, and forwards structured snippets into the context store.
- **Speech Recognition Layer** (upcoming) will transcribe audio tracks and attach text spans to the same timeline entries as their visual counterparts.
- **Unified Retrieval API** exposes both cyberspace and real-life context through a single search and recommendation surface.

Refer to `opencontext/` for CLI entry points, managers, storage adapters, and utilities; configuration files live under `config/`, while runtime data persists in `persist/` and `logs/`.

## Contributing

We welcome issues and pull requests focused on expanding context capture, improving retrieval, or polishing the smart glasses workflow. Please review `CONTRIBUTING.md` and follow the repository's testing and Conventional Commit guidelines.

## License

This project inherits the original MineContext license. See [LICENSE](LICENSE) for details.
