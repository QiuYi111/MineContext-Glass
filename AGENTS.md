# Repository Guidelines

## Project Structure & Module Organization
- `opencontext/` contains the core package (CLI entry point, server routes, managers, storage, and utilities).
- `config/` stores YAML configs and prompt templates consumed by the CLI (`config/config.yaml`, `prompts_*.yaml`).
- `src/` holds visual assets and docs; `screenshots/` provides UI examples. PyInstaller outputs land in `dist/` after builds.
- Local runtime data is written to `persist/` and `logs/`; keep them out of commits. Add new tests under `tests/` mirroring package paths.

## Build, Test, and Development Commands
- `uv sync` installs dependencies into the managed environment.
- `uv run opencontext start --port 8000` runs the server; add `--config config/config.yaml` to override settings.
- `python -m venv .venv && source .venv/bin/activate && pip install -e .` sets up a virtualenv alternative.
- `./build.sh` creates the PyInstaller bundle in `dist/` and copies required configs.

## Coding Style & Naming Conventions
- Target Python ≥3.9 with PEP 8 spacing (4 spaces) and ~100-character lines.
- Use explicit imports, type hints, and focused modules. Name modules/functions in `snake_case`, classes in `CamelCase`, constants in `UPPER_SNAKE_CASE`.
- Prefer succinct comments for non-obvious logic and keep files ASCII unless project context requires otherwise.

## Testing Guidelines
- Use `pytest -q` for the test suite. Place files as `tests/<module_path>/test_*.py` with functions named `test_*`.
- Strive for ≥80% coverage on new or modified code paths. Add fixtures or mocks alongside the relevant test modules.

## Commit & Pull Request Guidelines
- Commit messages follow Conventional Commits (e.g., `feat: add context manager`), imperative mood, ≤72 characters.
- PRs should link issues, describe rationale and impact, call out config or migration changes, and include screenshots for UI-impacting work.
- Keep scope tight; document manual testing or coverage notes in the PR body.

## Security & Configuration Tips
- Never commit secrets; store API keys locally in `config/config.yaml`.
- Common CLI flags: `--host`, `--port`, `--config`. CLI arguments take precedence over config files.
- Review `persist/` and `logs/` before sharing artifacts; redact sensitive context capture data.

## Architecture Overview
- Core pipeline: `context_capture` → `context_processing` → storage → server routes → downstream consumers.
- Entry point is the `opencontext` CLI (`opencontext.cli:main`). Consult `README.md` for usage patterns and integration examples.
