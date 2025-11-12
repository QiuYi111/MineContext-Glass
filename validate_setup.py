#!/usr/bin/env python3
"""
Simple validation script to verify MineContext Glass setup.
Run this after quick_setup.sh to confirm everything is working.
"""

import subprocess
import sys
import shutil
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - OK")
            return True
        else:
            print(f"❌ {description} - Failed")
            if result.stderr:
                print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False

def main():
    """Run validation checks."""
    print("🧪 MineContext Glass - Setup Validation")
    print("=" * 40)

    all_passed = True

    # Check 1: Python environment
    print("\n1. Python Environment:")
    all_passed &= run_command("python --version", "Python version check")

    # Check 2: uv package manager
    print("\n2. Package Manager:")
    all_passed &= run_command("uv --version", "uv package manager")

    # Check 3: Dependencies
    print("\n3. Dependencies:")
    all_passed &= run_command("uv run python -c 'import glass; print(\"Glass module OK\")'", "Glass module import")

    # Check 4: FFmpeg
    print("\n4. Video Processing:")
    all_passed &= run_command("ffmpeg -version | head -n1", "FFmpeg installation")

    # Check 5: Configuration
    print("\n5. Configuration:")
    config_exists = Path("config/config.yaml").exists()
    if config_exists:
        print("✅ Configuration file exists")
    else:
        print("❌ Configuration file missing")
        all_passed = False

    # Check 6: Glass CLI
    print("\n6. Glass CLI:")
    all_passed &= run_command("uv run glass --help | head -n5", "Glass CLI help")

    # Check 7: Integration test (lightweight)
    print("\n7. Integration Test:")
    all_passed &= run_command("uv run python -c 'from opencontext.server.utils import convert_resp; print(\"Server utils OK\")'", "Server utilities")

    # Summary
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All validation checks passed!")
        print("\n🚀 You're ready to use MineContext Glass!")
        print("\nNext steps:")
        print("1. Start the server: uv run opencontext start --port 8000 --config config/config.yaml")
        print("2. Process a video: uv run glass start 12-11")
        print("3. Or use WebUI: cd glass/webui && npm run dev")
        return 0
    else:
        print("❌ Some validation checks failed.")
        print("\n🔧 Please check the errors above and:")
        print("1. Run ./quick_setup.sh again")
        print("2. Check README_QUICK_START.md")
        print("3. Report issues on GitHub")
        return 1

if __name__ == "__main__":
    sys.exit(main())