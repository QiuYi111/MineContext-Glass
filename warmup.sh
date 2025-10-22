#!/usr/bin/env bash
set -euo pipefail

SESSION_NAME=${1:-opencontext-warmup}

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is required for warmup sessions." >&2
  exit 1
fi

if tmux has-session -t "$SESSION_NAME" >/dev/null 2>&1; then
  echo "tmux session \"$SESSION_NAME\" already exists."
  exit 0
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
START_CMD=$'uv run python - <<\'PY\'\nimport time\nimport torchaudio\nfrom whisperx.diarize import DiarizationPipeline\n\n_ = torchaudio.list_audio_backends()\n_ = DiarizationPipeline\nprint("WhisperX diarization warmup complete. Attach with: tmux attach -t '"$SESSION_NAME"'")\nwhile True:\n    time.sleep(3600)\nPY'

tmux new-session -d -s "$SESSION_NAME" "cd \"$ROOT_DIR\" && $START_CMD"
echo "Started tmux session \"$SESSION_NAME\" for WhisperX warmup."
