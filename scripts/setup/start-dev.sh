#!/bin/bash

# MineContext Glass Development Server Startup Script
# This script starts the backend server and WebUI frontend in separate tmux panes

set -e

echo "Starting MineContext Glass development servers..."

# Create a new tmux session named 'glass-dev' or attach to existing one
tmux new-session -d -s glass-dev -n "backend" -c "$PWD"

# Start backend server in first pane (no capture mode for glass backend)
tmux send-keys -t glass-dev:backend "uv run opencontext start --port 8000 --config config/config.yaml --no-capture" C-m

# Split window and create WebUI pane
tmux split-window -v -t glass-dev:backend -c "$PWD/glass/webui"
tmux rename-window -t glass-dev:backend "glass-dev"

# Start WebUI frontend in second pane
tmux send-keys -t glass-dev:glass-dev.1 "npm run dev" C-m

# Select the top pane by default
tmux select-pane -t glass-dev:glass-dev.0

# Attach to the session and then detach (so it runs in background)
tmux attach-session -t glass-dev
tmux detach-client -s glass-dev

echo "Development servers started in tmux session 'glass-dev'"
echo "To attach: tmux attach-session -t glass-dev"
echo "To kill session: tmux kill-session -t glass-dev"