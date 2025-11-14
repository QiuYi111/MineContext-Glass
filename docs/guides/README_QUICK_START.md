# MineContext Glass - Quick Start Guide

**🚀 Get started in 2 minutes with Glass CLI or WebUI**

<div align="center">
  <img alt="MineContext" src="../../assets/MineContext%20Glass.png" width="100%" height="auto">

  **Full-Spectrum Personal Context OS for Smart Glasses**
</div>

## 🎯 Quick Start Options

Choose your preferred way to interact with MineContext Glass:

### Option 1: Glass CLI (Recommended for Power Users)
**⚡ Process videos and generate reports in one command**

```bash
# 1. Start the server
uv run opencontext start --port 8000 --config config/config.yaml

# 2. Process videos for a specific date (dd-mm format)
uv run glass start 12-11 --config config/config.yaml

# 3. View generated report
open persist/reports/12-11.md
```

### Option 2: WebUI (Recommended for Interactive Use)
**🌐 Drag-and-drop interface with real-time processing**

```bash
# 1. Start the server (includes WebUI)
uv run opencontext start --port 8000 --config config/config.yaml

# 2. Start WebUI frontend
cd glass/webui && npm run dev

# 3. Open browser
open http://localhost:5174
```

## 📋 Prerequisites (1-minute setup)

```bash
# 1. Install uv package manager (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install dependencies
uv sync

# 3. Install FFmpeg (required for video processing)
# macOS:
brew install ffmpeg
# Ubuntu/Debian:
sudo apt install ffmpeg
```

## 🔑 First-Time Setup (30 seconds)

### 1. Get AUC Turbo Credentials
```bash
# Sign up at https://openspeech.bytedance.com
export AUC_APP_KEY=your-app-key-here
export AUC_ACCESS_KEY=your-access-key-here
```

### 2. Copy Configuration Template
```bash
cp config/config.yaml.example config/config.yaml
```

### 3. Verify Installation
```bash
uv run glass --help
```

## 🚀 Glass CLI Quick Commands

### Process Daily Videos
```bash
# Process videos from November 12th
uv run glass start 12-11

# Process with custom settings
uv run glass start 12-11 --lookback-minutes 180 --output my-report.md
```

### Generate Reports
```bash
# Create detailed report for a timeline
uv run python -m opencontext.cli glass report \
  --timeline-id 12-11 \
  --lookback-minutes 120 \
  --output my-daily-summary.md
```

### Check Processing Status
```bash
# Check if server is running
curl http://localhost:8000/health

# Get upload limits
curl http://localhost:8000/glass/uploads/limits
```

## 🌐 WebUI Quick Actions

### Upload Videos
1. Navigate to http://localhost:5174
2. Drag and drop video files
3. Monitor processing progress
4. View generated timeline

### Browse Timelines
1. Click on processed timelines
2. View highlights and summaries
3. Download reports as Markdown
4. Search through your context

## 📁 File Organization

```
videos/                    # Input videos
├── 12-11/                # Date-based folders
│   ├── video1.mp4
│   └── video2.mov
persist/                   # Generated content
├── glass/                # Processing data
├── reports/              # Final reports
└── contexts/             # Context storage
```

## 🎬 Supported Video Formats

- **MP4** (recommended)
- **MOV** (iPhone/iPad)
- **MKV** (Matroska)
- **Maximum size:** 2GB per file
- **Maximum duration:** 2 hours per file

## ⚡ Performance Tips

### For Large Video Collections
```bash
# Process multiple days in parallel
for day in {01..07}; do
  uv run glass start $day-11 &
done
wait
```

### For Faster Processing
```bash
# Skip speech recognition (video-only)
# Edit config.yaml and set fallback_enabled: true
```

### For Development
```bash
# Run in demo mode (no real processing)
export GLASS_BACKEND_MODE=demo
uv run glass start 12-11
```

## 🔧 Troubleshooting

### Server Won't Start
```bash
# Check if port 8000 is available
lsof -i :8000

# Try different port
uv run opencontext start --port 8001
```

### Videos Not Processing
```bash
# Check FFmpeg installation
ffmpeg -version

# Verify video format
ffprobe your-video.mp4
```

### AUC Turbo Errors
```bash
# Verify credentials
echo $AUC_APP_KEY
echo $AUC_ACCESS_KEY

# Check quotas and limits
cat glass/new_auc.md
```

### WebUI Not Loading
```bash
# Check Node.js installation
cd glass/webui && npm --version

# Reinstall dependencies
cd glass/webui && npm install
```

## 📚 Next Steps

### Advanced Configuration
- Edit `config/config.yaml` for custom settings
- See `glass/new_auc.md` for AUC Turbo configuration
- Check `TECH_DEBT_CLEANUP.md` for technical details

### Integration Options
- **MCP Server:** Use with Claude Desktop
- **API Integration:** Direct HTTP API calls
- **Custom Processing:** Build your own pipelines

### Contributing
- Report issues on GitHub
- Submit pull requests
- Join the community discussions

## 🆘 Quick Help

**Need immediate assistance?**

1. **Check the logs:** `tail -f logs/opencontext.log`
2. **Run diagnostics:** `uv run python test_webui_integration.py`
3. **Verify setup:** `uv run python -c "import glass; print('OK')"`

**Get help:**
- 📖 Full documentation: See original README.md
- 🐛 Report issues: GitHub Issues
- 💬 Community: GitHub Discussions

---

**Ready to transform your daily videos into searchable context? Let's go! 🚀**