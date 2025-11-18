# Project Index: MineContext Glass

**Generated:** 2025-01-18
**Description:** A glasses-first personal context platform that transforms daily life video streams from smart glasses into an organized, searchable knowledge base

## 📁 Project Structure

```
MineContext-Glass/
├── 🚀 Entry Points
│   ├── opencontext/cli.py          # Main CLI entry point
│   ├── glass/cli.py               # Glass-specific CLI wrapper
│   ├── electron/main.js           # Electron main process
│   ├── backend/main.py            # FastAPI backend server
│   └── webui/src/main.tsx         # React frontend entry
│
├── 📦 Core Architecture
│   ├── opencontext/               # Core 5-layer context framework
│   │   ├── context_capture/       # Layer 1: Data collection
│   │   ├── context_processing/    # Layer 2: Data processing
│   │   ├── storage/               # Layer 3: Data storage
│   │   ├── context_consumption/   # Layer 4: Data consumption
│   │   └── server/                # Layer 5: API services
│   │
│   ├── glass/                     # Video-first extension
│   │   ├── ingestion/             # Video processing pipeline
│   │   ├── processing/            # Glass-specific processing
│   │   ├── storage/               # Timeline-based storage
│   │   ├── consumption/           # Report generation
│   │   └── reports/               # Daily report service
│   │
│   ├── webui/                     # React + TypeScript frontend
│   │   ├── src/components/        # UI components
│   │   ├── src/api/              # API client
│   │   └── src/stores/           # State management
│   │
│   └── electron/                  # Desktop app wrapper
│
├── 🔧 Configuration & Data
│   ├── config/config.yaml         # Main configuration
│   ├── persist/                   # Local storage (SQLite + ChromaDB)
│   ├── videos/                    # Raw video files
│   ├── screenshots/               # Captured screenshots
│   └── assets/                    # App icons and resources
│
└── 🧪 Testing & Tools
    ├── tests/                     # Comprehensive test suite
    ├── auc_python/               # Speech recognition integration
    └── signatures/               # Code signing certificates
```

## 🚀 Entry Points

### CLI Applications
- **`opencontext/cli.py`** - Main CLI server with FastAPI backend
  - Commands: `start`, `glass report`, `glass start`
  - Web server on port 8765 (configurable)
  - Multi-process support with worker processes

- **`glass/cli.py`** - Glass-specific CLI wrapper
  - Thin wrapper around opencontext CLI
  - Command: `glass start <dd-mm>` for video processing

### Desktop Application
- **`electron/main.js`** - Electron main process
  - Auto-detects backend and frontend ports
  - Manages Python backend subprocess
  - Handles development/production modes

### Web Frontend
- **`webui/src/main.tsx`** - React application entry
  - Vite development server (port 5174)
  - TypeScript + React 18 + Zustand state management

## 📦 Core Modules

### OpenContext Framework (opencontext/)
**Purpose:** General-purpose context management system

#### Module: `context_capture/`
- **Exports:** ScreenshotCapture, FileMonitor, VaultDocumentMonitor
- **Purpose:** Collect context from screenshots, files, and document vaults
- **Key Classes:** BaseCapture (interface), ScreenshotCapture

#### Module: `context_processing/`
- **Exports:** DocumentProcessor, ScreenshotProcessor, ContextMerger
- **Purpose:** Process raw context into structured, searchable data
- **Key Classes:** BaseProcessor, EntityProcessor, LLMDocumentChunker

#### Module: `storage/`
- **Exports:** StorageManager, VectorDBBackend, DocumentDBBackend
- **Purpose:** Persist processed context with vector and document storage
- **Backends:** ChromaDB (vector), SQLite (document)

#### Module: `context_consumption/`
- **Exports:** ContextAgent, CompletionService, ReportGenerator
- **Purpose:** Consume context through AI agents, search, and reports
- **Key Features:** Smart completion, activity monitoring, todo generation

#### Module: `server/`
- **Exports:** FastAPI routes, middleware, OpenContext server
- **Purpose:** HTTP API and real-time services
- **Routes:** `/context`, `/chat`, `/agent`, `/debug`

### Glass Extension (glass/)
**Purpose:** Video-first context capture for smart glasses

#### Module: `ingestion/`
- **Exports:** VideoManager, AUCRunner, SpeechToText
- **Purpose:** Process video files, extract audio, transcribe speech
- **Dependencies:** FFmpeg, AUC Turbo API

#### Module: `processing/`
- **Exports:** VideoChunker, VisualEncoder, EnvelopeProcessor
- **Purpose:** Create timeline-aligned context chunks from video
- **Key Features:** Frame sampling, audio alignment, metadata enrichment

#### Module: `storage/`
- **Exports:** GlassContextRepository, TimelineModels
- **Purpose:** Timeline-based storage optimized for video context
- **Schema:** Timeline, ContextChunk, MediaMetadata

#### Module: `consumption/`
- **Exports:** GlassContextSource, ReportService
- **Purpose:** Generate intelligent reports from video timelines
- **Integration:** Doubao VLM for visual analysis

#### Module: `reports/`
- **Exports:** DailyReportService, SmartTipGenerator
- **Purpose:** Automated daily activity reports and insights
- **Output:** Markdown reports with timeline summaries

### Frontend (webui/)
**Purpose:** React-based web interface for video management

#### Module: `src/components/`
- **Exports:** VideoUploader, TimelineView, ReportViewer
- **Purpose:** UI components for video upload and management
- **Technology:** React 18, TypeScript, Framer Motion

#### Module: `src/api/`
- **Exports:** ApiClient, UploadService, TimelineService
- **Purpose:** HTTP client for backend communication
- **Features:** Multipart uploads, progress tracking, error handling

## 🔧 Configuration

### Main Configuration Files

- **`config/config.yaml`** - Primary configuration
  - Database paths, API keys, service ports
  - Feature flags and processing parameters
  - Model configurations (VLM, embedding, speech-to-text)

- **`pyproject.toml`** - Python project configuration
  - Dependencies: FastAPI, ChromaDB, FFmpeg, AUC Turbo
  - Scripts: `opencontext`, `glass` CLI commands
  - Development dependencies: PyInstaller, pytest

- **`package.json`** - Electron + Node.js configuration
  - Main: `electron/main.js` (desktop app)
  - Scripts for development, building, and packaging
  - Electron Builder configuration for macOS

### Key Configuration Sections

#### Logging
```yaml
logging:
  level: DEBUG
  # Structured logging with Loguru
```

#### Storage Backends
```yaml
storage:
  backends:
    - name: "default_vector"
      backend: "chromadb"
      path: "${CONTEXT_PATH:.}/persist/chromadb"
    - name: "document_store"
      backend: "sqlite"
      path: "${CONTEXT_PATH:.}/persist/sqlite/app.db"
```

#### AI Services
```yaml
vlm_model:
  provider: doubao
  model: doubao-seed-1-6-flash-250828
glass:
  speech_to_text:
    provider: auc_turbo
    base_url: https://openspeech.bytedance.com/api/v3
```

## 📚 Documentation

### Core Documentation
- **`README.md`** - Project overview and setup
- **`CLAUDE.md`** - Development guidelines and code philosophy
- **`docs/AGENTS.md`** - AI agent architecture and patterns
- **`docs/macOS-App-Packaging-Guide.md`** - Build and packaging instructions

### API Documentation
- **`docs/api_reference_zh.md`** - Chinese API reference
- **`docs/glass_*_api.md`** - Glass extension API docs
- **`docs/video_manager_api.md`** - Video processing API

### Development Guides
- **`docs/guides/`** - Development and contribution guides
- **`Electron开发指南.md`** - Electron development guide (Chinese)
- **`docs/usage/capture_control.md`** - Context capture usage

## 🧪 Test Coverage

### Test Structure
- **Unit tests:** 25+ test modules
- **Integration tests:** WebUI, configuration, speech processing
- **Test files:** `tests/glass/`, `tests/integration/`
- **Coverage:** 80%+ minimum for new code

### Key Test Modules
- **`tests/glass/ingestion/`** - Video processing tests
- **`tests/glass/consumption/`** - Report generation tests
- **`tests/integration/`** - End-to-end integration tests
- **`conftest.py`** - Shared test fixtures and utilities

### Running Tests
```bash
# Run all tests
uv run pytest

# Skip slow video tests
uv run pytest -m "not slow"

# Specific modules
uv run pytest tests/glass/ingestion/
uv run pytest tests/integration/
```

## 🔗 Key Dependencies

### Python Backend (pyproject.toml)
- **FastAPI** (web framework) - REST API and async processing
- **ChromaDB** (vector database) - Semantic search and embeddings
- **Polars** (data processing) - High-performance data analysis
- **FFmpeg** (media processing) - Video/audio extraction and processing
- **AUC Turbo** (speech recognition) - ByteDance's speech-to-text API
- **Doubao VLM** (vision model) - Visual understanding for reports

### Frontend (webui/package.json)
- **React 18** + **TypeScript** - UI framework and type safety
- **Vite** - Fast development server and build tool
- **Zustand** - Lightweight state management
- **Framer Motion** - Smooth animations and transitions
- **date-fns** - Date manipulation utilities

### Desktop (package.json)
- **Electron** - Cross-platform desktop application framework
- **Electron Builder** - Application packaging and distribution

### Development Tools
- **uv** - Fast Python package manager (required)
- **PyInstaller** - Python application packaging
- **pytest** - Testing framework with async support

## 📝 Quick Start

### Environment Setup
```bash
# Install Python dependencies
uv sync

# Set AUC Turbo credentials (required for speech recognition)
export AUC_APP_KEY=your-app-key
export AUC_ACCESS_KEY=your-access-key
```

### Development Workflow

#### Backend Development
```bash
# Start OpenContext server (no capture mode)
uv run opencontext start --port 8000 --config config/config.yaml --no-capture

# Process video for specific date (dd-mm format)
uv run glass start 22-10 --config config/config.yaml

# Generate glass report
uv run python -m opencontext.cli glass report --timeline-id <timeline> --lookback-minutes 120
```

#### Frontend Development
```bash
cd webui
npm install
npm run dev        # Development server on port 5174
npm run build      # Production build
```

#### Desktop Application
```bash
# Development mode with hot reload
npm run electron-dev

# Production build and package
npm run build
```

### Testing
```bash
# Run all tests
uv run pytest

# Start development services
npm run start     # Starts both backend and frontend
```

## 🔗 Integration Points

### Video Processing Pipeline
```
Video Files → FFmpeg → Frame Extraction + Audio → AUC Turbo → Transcript → Timeline Context → Storage
```

### Report Generation Flow
```
Timeline Context → Visual Encoder → Doubao VLM → Smart Analysis → Markdown Report
```

### Frontend-Backend Communication
```
React UI → HTTP API → FastAPI → Context Services → Storage (ChromaDB + SQLite)
```

## ⚡ Performance Optimizations

- **Vector Database**: ChromaDB with local persistence for fast semantic search
- **Batch Processing**: Configurable batch sizes for document and screenshot processing
- **Async Operations**: Full async/await support throughout the pipeline
- **Memory Management**: Automatic cleanup and retention policies
- **Caching**: Multi-level caching for embeddings, API responses, and completions

## 🔒 Security & Privacy

- **Local-First**: All processing happens locally, no cloud dependencies
- **No Telemetry**: No usage data or analytics collection
- **API Key Protection**: Environment variable-based credential management
- **File Access**: Sandboxed file access with explicit path configuration
- **Code Signing**: macOS application signing for distribution security