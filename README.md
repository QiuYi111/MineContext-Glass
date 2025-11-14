<div align="center">

![MineContext Glass](assets/MineContext%20Glass.png)

### MineContext Glass: Full-Spectrum Personal Context OS

Built on ByteDance's [MineContext](https://github.com/volcengine/MineContext), extending the original open-source project into a glasses-first personal context platform.

</div>

<p align="center">
  <a href="#quick-start">🚀 Quick Start (2 minutes)</a> •
  <a href="#中文快速开始">中文文档</a> •
  <a href="docs/guides/README_QUICK_START.md">📖 Detailed Guide</a>
</p>

<p align="center">
  <img alt="Python 3.9+" src="https://img.shields.io/badge/python-3.9%2B-blue.svg">
  <img alt="uv managed env" src="https://img.shields.io/badge/uv-managed%20env-6f42c1.svg">
  <img alt="ffmpeg required" src="https://img.shields.io/badge/ffmpeg-required-brightgreen.svg">
  <img alt="AUC Turbo" src="https://img.shields.io/badge/AUC%20Turbo-required%20API-red.svg">
</p>

## 🚀 Quick Start (Choose Your Path)

### Option 1: Glass CLI - Process Videos in One Command
```bash
# 1. Start server
uv run opencontext start --port 8000 --config config/config.yaml

# 2. Process videos for November 12th
uv run glass start 12-11

# 3. View report
open persist/reports/12-11.md
```

### Option 2: WebUI - Drag & Drop Interface
```bash
# 1. Start server
uv run opencontext start --port 8000 --config config/config.yaml

# 2. Start WebUI
cd webui && npm run dev

# 3. Open browser to http://localhost:5174
```

**🔗 [Full Quick Start Guide →](docs/guides/README_QUICK_START.md)**

**📦 [Setup Script → scripts/setup/quick_setup.sh]** • **✅ [Validation → scripts/setup/validate_setup.py]**

## 中文快速开始 {#中文快速开始}

### 🎯 两种使用方式

**方式1：命令行 (适合高级用户)**
```bash
# 1. 启动服务
uv run opencontext start --port 8000 --config config/config.yaml

# 2. 处理11月12日的视频
uv run glass start 12-11

# 3. 查看报告
open persist/reports/12-11.md
```

**方式2：网页界面 (适合交互使用)**
```bash
# 1. 启动服务
uv run opencontext start --port 8000 --config config/config.yaml

# 2. 启动网页界面
cd webui && npm run dev

# 3. 打开浏览器访问 http://localhost:5174
```

### 🔑 首次设置 (30秒)

```bash
# 1. 获取 AUC Turbo 凭证
export AUC_APP_KEY=你的应用密钥
export AUC_ACCESS_KEY=你的访问密钥

# 2. 复制配置模板
cp config/config.yaml.example config/config.yaml

# 3. 验证安装
uv run glass --help
```

**🔗 [完整中文文档 →](README_zh.md)**

## 📋 Prerequisites (30-second setup)

### 🚀 Super Quick Setup (Recommended)
```bash
# 1. Run our automated setup script
./quick_setup.sh

# 2. Validate installation
uv run python validate_setup.py
```

### Manual Setup (If you prefer)
```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Install FFmpeg
brew install ffmpeg  # macOS
# sudo apt install ffmpeg  # Ubuntu/Debian
```

## 🎯 What You Get

- **📹 Video Processing:** Transform daily recordings into searchable context
- **🗣️ Speech Recognition:** AUC Turbo transcription for audio content
- **🔍 Smart Search:** Find moments across your visual memory
- **📊 Daily Reports:** AI-generated summaries of your day
- **🌐 Web Interface:** Drag-and-drop video processing
- **⚡ CLI Tools:** Batch processing and automation

## 🏗️ Architecture Overview

```
Smart Glasses → Video Capture → Frame Extraction → Speech Recognition → Context Storage → Search & Reports
```

**Key Components:**
- **Video Pipeline:** FFmpeg-based processing with adaptive sampling
- **Speech Layer:** Doubao AUC Turbo for transcription
- **Context Engine:** Unified storage with MineContext foundation
- **WebUI:** React frontend with real-time processing
- **CLI Tools:** Command-line interface for batch operations

## 🛠️ Current Capabilities

- ✅ **Video Ingestion:** MP4/MOV/MKV support, up to 2GB per file
- ✅ **Speech Recognition:** AUC Turbo integration for audio transcription
- ✅ **Frame Extraction:** Adaptive sampling for optimal context density
- ✅ **Timeline Generation:** Chronological organization with highlights
- ✅ **Report Generation:** Markdown summaries with visual cards
- ✅ **Web Interface:** Interactive upload and browsing
- ✅ **CLI Processing:** Batch operations and automation

## 📊 Technical Improvements (Recent)

Following Linus Torvalds' code audit recommendations:

- ✅ **Architecture Simplified:** 4-layer → 2-layer design
- ✅ **Race Conditions Fixed:** Atomic state management
- ✅ **Single Points Eliminated:** Speech recognition fallback
- ✅ **Configuration Unified:** Single GlobalConfig system
- ✅ **Reliability Enhanced:** Graceful error handling

## 🎯 Next Steps

1. **Try it:** Follow the [Quick Start Guide](README_QUICK_START.md)
2. **Configure:** Set up AUC Turbo credentials
3. **Process:** Upload your first video
4. **Explore:** Search through your visual context

## 📚 Documentation

- **🔧 Setup:** [Quick Start Guide](docs/guides/README_QUICK_START.md)
- **📖 Details:** [Full Documentation](#detailed-documentation) below
- **🇨🇳 中文:** [Chinese Documentation](README_zh.md)
- **🐛 Issues:** [GitHub Issues](https://github.com/your-repo/issues)
- **💬 Community:** [GitHub Discussions](https://github.com/your-repo/discussions)

---

## Detailed Documentation

### 📖 Table of Contents

- [Vision](#vision)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Start the Pipeline](#start-the-pipeline)
- [Speech Recognition with AUC Turbo](#speech-recognition-with-auc-turbo)
- [Generate Glass Reports](#generate-glass-reports)
- [Frame-Only Ingest (Legacy)](#frame-only-ingest-legacy)
- [Architecture](#architecture)
- [Contributing](#contributing)

---

## 详细文档 (中文) {#detailed-documentation-zh}

**🔗 [查看完整中文文档 →](README_zh.md)**

---

## Vision

MineContext Glass reimagines personal context management around daily life. Using smart glasses, we capture day-long video streams and transform them into an organized, searchable knowledge base that bridges the physical and digital worlds. Every clip becomes part of a living memory system that powers summaries, reminders, and intelligent recommendations.

By standing on MineContext's mature context engineering foundations, we combine the existing cyberspace context (screen captures, documents, chats) with real-life visuals to create a full-spectrum, proactive assistant. The next milestone is speech recognition extracted from captured video audio, so conversations and spoken cues join the same context graph.

### Prerequisites

- macOS or Linux with Python 3.9+.
- `uv` package manager (recommended) or a Python virtual environment.
- `ffmpeg` and `ffprobe` available on `PATH` (for example `brew install ffmpeg` on macOS).
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
3. Configure the Glass block so AUC Turbo credentials are available:

```yaml
glass:
  speech_to_text:
    provider: auc_turbo
    auc_turbo:
      base_url: https://openspeech.bytedance.com/api/v3
      resource_id: volc.bigasr.auc_turbo
      app_key: "${AUC_APP_KEY:}"
      access_key: "${AUC_ACCESS_KEY:}"
      request_timeout: 120
      max_file_size_mb: 100
      max_duration_sec: 7200
```

Credentials can live in the config file, environment variables, or be passed as CLI flags. See [docs/api/GLASS_AUDIT_REPORT.md](docs/api/GLASS_AUDIT_REPORT.md) for quotas, error codes, and troubleshooting tips.

### Start the Pipeline

Run the context server with:

```bash
uv run opencontext start --port 8000 --config config/config.yaml
```

Glasses footage dropped into the configured import path will be processed automatically. Use the CLI or API endpoints to inspect timelines, digests, and retrieved clips.

### Speech Recognition with AUC Turbo

1. Export the required credentials (or supply them via CLI flags):

   ```bash
   export AUC_APP_KEY=your-app-key
   export AUC_ACCESS_KEY=your-access-key
   ```

2. Launch the production pipeline against a specific date folder. The new `glass`
   entry point maps directly to the OpenContext CLI and processes everything under
   `videos/<dd-mm>/`:

   ```bash
   uv run glass start dd-mm --config config/config.yaml
   ```

   Results are written to the unified storage configured by `CONTEXT_PATH`, and
   timeline reports are collected under `persist/reports/dd-mm/`. Pass `--report-output`
   to override the destination directory or `--lookback-minutes` to adjust the window
   used for report generation.

### Generate Glass Reports

Once a timeline has been ingested, you can produce scoped summaries directly from the CLI:

```bash
uv run python -m opencontext.cli glass report \
  --timeline-id <timeline> \
  --lookback-minutes 120 \
  --output persist/reports/<timeline>.md
```

The report command reads the contexts persisted by the Glass timeline processor and writes Markdown files suitable for sharing.

### Frame-Only Ingest (Legacy)

If you only need frame extraction (for example, benchmarking embedding throughput), place raw `.mp4` files under `videos/<DATE>/` (such as `videos/2025-02-27/12-13.mp4`) and run:

```bash
uv run opencontext.tools.daily_vlog_ingest
```

This legacy tool extracts frames, updates the context store, and writes summaries to `persist/reports/<date>.md`. Speech recognition is no longer performed here; the Glass ingestion flow handles it through AUC Turbo when you process the resulting timelines.

## Architecture

MineContext Glass keeps the original context-flow of `context_capture → context_processing → storage → server routes`, expanding the capture stage with a dedicated video manager.

- **Video Capture Manager** (upcoming) pulls footage from smart glasses, handles deduplication, and writes raw assets to managed storage.
- **Video Processing Pipeline** extracts frames, runs embeddings, and forwards structured snippets into the context store.
- **Speech Recognition Layer** (AUC Turbo) transcribes audio tracks via Doubao AUC Turbo and attaches aligned text spans to the same timeline entries as their visual counterparts.
- **Unified Retrieval API** exposes both cyberspace and real-life context through a single search and recommendation surface.

Refer to `opencontext/` for CLI entry points, managers, storage adapters, and utilities; configuration files live under `config/`, while runtime data persists in `persist/` and `logs/`.

---

## 📚 文档导航

### 语言版本
- **English**: 当前文档
- **中文**: [README_zh.md](README_zh.md) - 完整中文文档

### 快速导航
- **🚀 快速开始**: [2分钟入门](docs/guides/README_QUICK_START.md)
- **🔧 设置指南**: [详细配置说明](#configuration)
- **🛠️ 故障排除**: [常见问题解决](docs/guides/README_QUICK_START.md#troubleshooting)
- **📊 技术审计**: [架构改进报告](docs/api/GLASS_AUDIT_REPORT.md)

### 核心功能
- **视频处理**: 支持MP4/MOV/MKV格式，最大2GB
- **语音识别**: AUC Turbo集成，音频转录
- **智能搜索**: 跨模态上下文检索
- **报告生成**: Markdown格式日常总结
- **网页界面**: 拖拽上传，实时处理

### 相关文档
- [CONTRIBUTING.md](docs/CONTRIBUTING.md) - 贡献指南
- [AGENTS.md](docs/AGENTS.md) - 代理说明
- [技术债务清理](docs/api/TECH_DEBT_CLEANUP.md) - 架构改进详情

## Contributing

We welcome issues and pull requests focused on expanding context capture, improving retrieval, or polishing the smart glasses workflow. Please review `CONTRIBUTING.md` and follow the repository's testing and Conventional Commit guidelines.

## License

This project inherits the original MineContext license. See [LICENSE](LICENSE) for details.
