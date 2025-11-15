# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MineContext Glass is a "glasses-first personal context platform" that transforms daily life video streams from smart glasses into an organized, searchable knowledge base. It extends ByteDance's MineContext project with video-first context capture capabilities.

## Development Commands

### Environment Setup
```bash
# Install dependencies using uv (required)
uv sync

# Set AUC Turbo credentials for speech recognition
export AUC_APP_KEY=your-app-key
export AUC_ACCESS_KEY=your-access-key
```

### Backend Development
```bash
# Start main context server (no capture mode for glass backend)
uv run opencontext start --port 8000 --config config/config.yaml --no-capture

# Process video for specific date (dd-mm format)
uv run glass start dd-mm --config config/config.yaml

# Generate glass report
uv run python -m opencontext.cli glass report --timeline-id <timeline> --lookback-minutes 120 --output persist/reports/<timeline>.md
```

### Frontend Development
```bash
cd glass/webui
npm install
npm run dev        # Development server on port 5174
npm run build      # Production build
npm run preview    # Preview production build
```

### Testing
```bash
# Run all tests
uv run pytest

# Skip slow video ingestion tests
uv run pytest -m "not slow"

# Run specific test modules
uv run pytest glass/tests/ingestion/
uv run pytest glass/tests/reports/
```

### Building
```bash
# Build executable with PyInstaller
./build.sh

# Result in dist/main, includes config and signatures
```

## Architecture Overview

### Core Pipeline Flow
```
context_capture → context_processing → context_storage → context_services → context_consumption
```

### Key Components

**OpenContext Core** (`opencontext/`)
- Five-layer architecture for general context management
- Handles screenshots, file monitoring, vault documents
- Vector DB + Document DB storage backends
- MCP server for application consumption

**Glass Extension** (`glass/`)
- Video ingestion pipeline with FFmpeg processing
- AUC Turbo speech recognition integration
- Timeline-based context organization
- Daily report generation

**WebUI** (`glass/webui/`)
- React + TypeScript frontend with Vite
- Video upload and management interface
- Report visualization and timeline browsing
- Zustand for state management

### Critical Integration Points

1. **Video Processing Pipeline**: `glass/ingestion/` → `opencontext/processing/` → storage
2. **Speech Recognition**: Audio extraction → AUC Turbo API → transcription storage
3. **Timeline Generation**: Video frames + audio → time-aligned context chunks
4. **Report Generation**: Context aggregation → Doubao VLM → markdown reports

### Current Technical Debt

**Backend Integration Gap**: The FastAPI backend in `glass/webui/backend/` serves mock JSON instead of real pipeline data. The TimelineRepository uses in-memory dict instead of GlassContextRepository.

**State Management**: No persistent state machine for upload tasks - tasks restart on server reload.

**Data Consistency**: CLI pipeline and WebUI backend use different data formats and storage mechanisms.

## Code Philosophy (from AGENTS.md)

This project follows Linus Torvalds' development philosophy:

1. **Good Taste**: Eliminate special cases, prefer clean data structures
2. **Never Break Userspace**: Backward compatibility is sacred
3. **Pragmatism**: Solve real problems, not theoretical ones
4. **Simplicity**: Functions should be short, do one thing well

When reviewing code:
- 🟢 Good taste: Clean, no special cases
- 🟡 Tolerable: Works but could be simpler
- 🔴 Garbage: Overly complex or breaks principles

## Key Technical Constraints

1. **uv Package Manager**: Always use `uv run` instead of direct python commands
2. **Python 3.9+**: Minimum version requirement
3. **FFmpeg Dependency**: Required for all video processing
4. **AUC Turbo API**: Speech recognition requires valid credentials
5. **Local-First**: All processing happens locally, no cloud dependencies

## Common Development Patterns

### Adding New Context Sources
1. Implement capture interface in `opencontext/capture/`
2. Add processing logic in `opencontext/processing/`
3. Update storage schema if needed
4. Add CLI command in `opencontext/cli.py`

### Modifying Video Pipeline
1. Ingestion logic: `glass/ingestion/`
2. Processing pipeline: `glass/processing/`
3. Storage integration: `glass/storage/`
4. Report generation: `glass/reports/`

### Frontend Changes
1. Components in `glass/webui/src/components/`
2. API calls through `glass/webui/src/api/`
3. State management in `glass/webui/src/stores/`
4. Backend mocks in `glass/webui/backend/` (replace with real integration)

## Testing Requirements

- Minimum 80% test coverage for new code
- Use pytest fixtures from `glass/tests/conftest.py`
- Mock external APIs (AUC Turbo, Doubao) in tests
- Test video processing with small sample files
- Verify FFmpeg integration with `pytest.mark.slow` tests

## Configuration Management

- Main config: `config/config.yaml`
- Environment variables override config file values
- Support for multiple languages (EN/ZH) in `config/prompts_*.yaml`
- AUC credentials must be set via environment variables

## Error Handling Principles

1. **Graceful Degradation**: If speech recognition fails, continue with video-only processing
2. **User Feedback**: Always provide clear error messages in CLI and UI
3. **Recovery**: Implement retry logic for external API calls
4. **Logging**: Use structured logging with appropriate levels
5. **Validation**: Validate all inputs before processing (video formats, date ranges, etc.)