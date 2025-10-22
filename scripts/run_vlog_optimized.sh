#!/usr/bin/env bash
set -euo pipefail

# Optimized wrapper for the MineContext vlog pipeline.
# Tuned to reduce backlog in screenshot/document processors by sampling fewer frames
# and relaxing WhisperX workloads. Override defaults via environment variables.

DATE_TOKEN="${1:-$(date +%d-%m)}"
shift || true

FRAME_INTERVAL="${FRAME_INTERVAL:-20}"
WHISPER_MODEL="${WHISPER_MODEL:-medium}"
BATCH_SIZE="${BATCH_SIZE:-8}"
MAX_WAIT="${MAX_WAIT:-600}"

YEAR_FLAG=()
if [[ "${DATE_TOKEN}" =~ ^[0-9]{2}-[0-9]{2}$ && -z "${YEAR:-}" ]]; then
  YEAR_FLAG=(--year "$(date +%Y)")
elif [[ -n "${YEAR:-}" ]]; then
  YEAR_FLAG=(--year "${YEAR}")
fi

uv run python -m opencontext.tools.vlog \
  --date "${DATE_TOKEN}" \
  "${YEAR_FLAG[@]}" \
  --frame-interval "${FRAME_INTERVAL}" \
  --whisper-model "${WHISPER_MODEL}" \
  --batch-size "${BATCH_SIZE}" \
  --no-align \
  --save-transcripts \
  --no-transcript-ingest \
  --max-wait "${MAX_WAIT}" \
  "$@"
