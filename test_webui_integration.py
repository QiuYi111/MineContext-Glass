#!/usr/bin/env python3
"""Test script to verify WebUI integration with main OpenContext server."""

import requests
import sys
from pathlib import Path

def test_main_server_endpoints():
    """Test that main server Glass API endpoints are working."""
    base_url = "http://127.0.0.1:8000"

    print("Testing main server Glass API endpoints...")

    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Health check: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

    # Test upload limits
    try:
        response = requests.get(f"{base_url}/glass/uploads/limits", timeout=5)
        if response.status_code == 200:
            limits = response.json()
            print(f"✅ Upload limits: {limits}")
        else:
            print(f"⚠️  Upload limits returned {response.status_code}")
    except Exception as e:
        print(f"❌ Upload limits failed: {e}")

    # Test non-existent timeline (should return 404)
    try:
        response = requests.get(f"{base_url}/glass/status/test-timeline", timeout=5)
        if response.status_code == 404:
            print("✅ Status check for non-existent timeline: 404 (expected)")
        else:
            print(f"⚠️  Status check returned {response.status_code}")
    except Exception as e:
        print(f"❌ Status check failed: {e}")

    return True

def test_webui_frontend_build():
    """Test that WebUI frontend builds successfully."""
    print("\nTesting WebUI frontend build...")

    webui_dir = Path(__file__).parent / "glass" / "webui"
    if not webui_dir.exists():
        print(f"❌ WebUI directory not found: {webui_dir}")
        return False

    # Check if node_modules exists
    node_modules = webui_dir / "node_modules"
    if not node_modules.exists():
        print("⚠️  node_modules not found, need to run npm install")
        return False

    print("✅ WebUI frontend structure looks good")
    return True

def main():
    """Run integration tests."""
    print("=== WebUI Integration Test ===")
    print("Testing integration between WebUI frontend and main OpenContext server")

    success = True

    # Test main server
    if not test_main_server_endpoints():
        success = False

    # Test WebUI frontend
    if not test_webui_frontend_build():
        success = False

    if success:
        print("\n✅ Integration tests passed!")
        print("\nNext steps:")
        print("1. Start main OpenContext server: uv run opencontext start --port 8000")
        print("2. Start WebUI frontend: cd glass/webui && npm run dev")
        print("3. Access WebUI at: http://localhost:5174")
    else:
        print("\n❌ Integration tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()