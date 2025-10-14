# Repository Guidelines

## Project Structure & Module Organization
- `opencontext/`: Core package (CLI, server routes, managers, context_capture, storage, llm, utils, tools).
- `config/`: YAML config and prompt templates (e.g., `config.yaml`, `prompts_*.yaml`).
- `src/`: Assets and docs (diagrams, GIFs); `screenshots/`: app UI examples.
- `build.sh` + `opencontext.spec`: Packaging with PyInstaller; outputs to `dist/`.
- `persist/`, `logs/`: Local data and logs; not for commits.

## Build, Test, and Development Commands
- Install deps (recommended): `uv sync`
- Run server: `uv run opencontext start --port 8000` or `--config config/config.yaml`
- Virtualenv alternative: `python -m venv .venv && source .venv/bin/activate && pip install -e . && opencontext start`
- Package app: `./build.sh` (produces `dist/main`; copies `config/`)

## Coding Style & Naming Conventions
- Python ≥3.9; follow PEP 8; 4-space indent; max line length ~100.
- Naming: modules/functions `snake_case`, classes `CamelCase`, constants `UPPER_SNAKE_CASE`.
- Use type hints, explicit imports, and small, focused modules.

## Testing Guidelines
- No repo-wide test suite yet. When adding tests, use `pytest`.
- Layout: mirror package paths, e.g., `tests/context_capture/test_screenshot.py`.
- Conventions: files `test_*.py`, functions `test_*`; run with `pytest -q`.
- Target >80% coverage for new/changed code paths.

## Commit & Pull Request Guidelines
- Commit messages: conventional prefixes (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `hotfix:`). Use imperative mood; keep subject ≤72 chars.
- Branch names: `feature/<name>`, `fix/<name>`, `docs/<name>`, etc.
- PRs: link issues, describe rationale and impact, list config changes/migrations, add screenshots for UI/behavioral updates. Keep scope focused.

## Security & Configuration Tips
- Do not commit secrets. Store API keys in local `config/config.yaml` only.
- Common options: `--host`, `--port`, `--config`. CLI args override config.
- `persist/` and `logs/` contain local artifacts; review before sharing.

## Architecture Overview
- Pipeline: context_capture → context_processing → storage → server/routes → context_consumption.
- Entry point: `opencontext` CLI (`opencontext.cli:main`). See `README.md` for details.

