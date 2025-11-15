#!/bin/bash

# MineContext Glass - Quick Setup Script
# This script gets you up and running in under 2 minutes

set -e

echo "🚀 MineContext Glass - Quick Setup"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Please run this script from the MineContext Glass root directory"
    exit 1
fi

# Step 1: Check prerequisites
echo "📋 Step 1: Checking prerequisites..."

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found. Please install Python 3.9+ first"
    exit 1
fi

echo "✅ Python found: $($PYTHON_CMD --version)"

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi
echo "✅ uv found: $(uv --version)"

# Step 2: Install dependencies
echo ""
echo "📦 Step 2: Installing dependencies..."
uv sync
echo "✅ Dependencies installed"

# Step 3: Check FFmpeg
echo ""
echo "🔧 Step 3: Checking FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg found: $(ffmpeg -version | head -n1)"
else
    echo "⚠️  FFmpeg not found. Please install it:"
    echo "   macOS: brew install ffmpeg"
    echo "   Ubuntu/Debian: sudo apt install ffmpeg"
    echo "   Or download from: https://ffmpeg.org/download.html"
fi

# Step 4: Setup configuration
echo ""
echo "⚙️  Step 4: Setting up configuration..."
if [ ! -f "config/config.yaml" ]; then
    if [ -f "config/config.yaml.example" ]; then
        cp config/config.yaml.example config/config.yaml
        echo "✅ Configuration file created from template"
    else
        echo "⚠️  Please create config/config.yaml manually"
    fi
else
    echo "✅ Configuration file already exists"
fi

# Step 5: Check AUC Turbo credentials
echo ""
echo "🔑 Step 5: Checking AUC Turbo credentials..."
if [ -n "$AUC_APP_KEY" ] && [ -n "$AUC_ACCESS_KEY" ]; then
    echo "✅ AUC credentials found in environment"
elif grep -q "your-app-key" config/config.yaml 2>/dev/null; then
    echo "⚠️  Please set your AUC Turbo credentials:"
    echo "   1. Get credentials from https://openspeech.bytedance.com"
    echo "   2. Export them: export AUC_APP_KEY=your-key"
    echo "   3. Or edit config/config.yaml directly"
else
    echo "✅ AUC credentials appear to be configured"
fi

# Step 6: Verify installation
echo ""
echo "🧪 Step 6: Verifying installation..."
if uv run glass --help &> /dev/null; then
    echo "✅ Glass CLI is working!"
else
    echo "❌ Glass CLI verification failed"
    exit 1
fi

# Final success message
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Quick start options:"
echo ""
echo "1. Glass CLI (process videos):"
echo "   uv run opencontext start --port 8000 --config config/config.yaml --no-capture"
echo "   uv run glass start 12-11  # Process videos from Nov 12th"
echo ""
echo "2. WebUI (drag & drop):"
echo "   cd glass/webui && npm install && npm run dev"
echo "   # Then open http://localhost:5174"
echo ""
echo "3. Test the setup:"
echo "   uv run python test_webui_integration.py"
echo ""
echo "📁 Your videos go in: videos/DD-MM/"
echo "📊 Reports appear in: persist/reports/"
echo "📁 Your videos go in: videos/DD-MM/"
echo "📊 Reports appear in: persist/reports/"
echo ""
echo "🚀 Ready to transform your videos into searchable context!"
echo ""
echo "Need help? Check README_QUICK_START.md or open an issue on GitHub."
