# MineContext Glass Module

MineContext Glass extends the existing MineContext pipeline to ingest first-person video and expose aligned multimodal context to downstream consumers without disturbing the legacy screenshot workflow.

## Directory Overview
- `ingestion/`: Video intake interfaces such as `VideoManager`, ffmpeg helpers, and AUC Turbo runners.
- `processing/`: Chunkers and encoders that convert manifests into embeddings.
- `storage/`: Repositories for persisting aligned segments and metadata.
- `ui/`: Glass-specific UI assets and front-end integrations.
- `docs/`: Design notes and operational runbooks for Glass modules.
- `scripts/`: Setup, tooling, and automation related to Glass deployment.
- `tests/`: Unit and integration tests validating the Glass pipeline.

## Usage
- Prefer importing shared functionality through `opencontext` packages; only Glass-specific functionality should live under this namespace.
- Configuration stays isolated under `config/glass.yaml` (to be introduced) so that the base MineContext experience remains unchanged unless Glass is explicitly enabled.
