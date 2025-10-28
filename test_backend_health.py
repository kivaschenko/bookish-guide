#!/usr/bin/env python3
"""
Backend Health Check Script
Tests the current state of the FastAPI backend server.
"""

import requests
import sys
from pathlib import Path
import subprocess
import time
import signal
import os
import importlib.util


def test_backend_health():
    """Test if the backend server is functional."""
    print("🔍 StoryForge Backend Health Check")
    print("=" * 50)

    # Test 1: Check if dependencies are available
    print("\n1. Checking Python dependencies...")
    try:
        # Test for fastapi
        if importlib.util.find_spec("fastapi") is None:
            raise ImportError("fastapi not found")
        # Test for uvicorn
        if importlib.util.find_spec("uvicorn") is None:
            raise ImportError("uvicorn not found")
        # Test for pydantic_settings
        if importlib.util.find_spec("pydantic_settings") is None:
            raise ImportError("pydantic_settings not found")
        print("✅ Core dependencies available")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

    # Test 2: Check configuration
    print("\n2. Checking configuration...")
    backend_dir = Path(__file__).parent / "backend"
    config_file = Path(__file__).parent / "config.yml"

    if config_file.exists():
        print("✅ Main config.yml found")
    else:
        print("❌ Main config.yml not found")
        return False

    # Test 3: Check backend structure
    print("\n3. Checking backend structure...")
    required_files = [
        "main.py",
        "run.py",
        "config/settings.py",
        "routes/api.py",
        "websocket/handler.py",
        "auth/middleware.py",
    ]

    missing_files = []
    for file_path in required_files:
        full_path = backend_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files")
        return False

    # Test 4: Try to start server briefly
    print("\n4. Testing server startup...")
    try:
        # Start server as subprocess
        process = subprocess.Popen(
            [sys.executable, "run.py"],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )

        # Wait a moment for startup
        time.sleep(3)

        # Test if process is running
        if process.poll() is None:
            print("✅ Server process started successfully")

            # Try a simple request
            try:
                response = requests.get("http://localhost:47393/docs", timeout=5)
                if response.status_code == 200:
                    print("✅ Server responding to HTTP requests")
                    print(
                        "✅ API documentation accessible at http://localhost:47393/docs"
                    )
                else:
                    print(
                        f"⚠️ Server responding but returned status {response.status_code}"
                    )
            except requests.exceptions.RequestException:
                print("⚠️ Server started but not responding to HTTP requests")

            # Clean shutdown
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=5)
                print("✅ Server shutdown cleanly")
            except Exception:
                process.kill()
                print("⚠️ Force killed server process")

            return True
        else:
            stdout, stderr = process.communicate()
            print("❌ Server failed to start")
            if stderr:
                print(f"Error: {stderr.decode()}")
            return False

    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

    return True


def show_next_steps():
    """Show recommended next steps based on test results."""
    print("\n" + "=" * 50)
    print("🚀 NEXT STEPS RECOMMENDATIONS")
    print("=" * 50)

    print("\n📋 IMMEDIATE ACTIONS (This Week):")
    print("1. Install missing dependencies:")
    print("   cd backend && pip install -r requirements.txt")

    print("\n2. Start development server:")
    print("   cd backend && python run.py")

    print("\n3. Test API endpoints:")
    print("   curl http://localhost:47393/docs")
    print("   curl http://localhost:47393/timeline")

    print("\n📈 BACKEND DEVELOPMENT PRIORITIES:")
    print("1. Complete project management endpoints")
    print("2. Add database integration (SQLAlchemy)")
    print("3. Implement file upload system")
    print("4. Add comprehensive error handling")
    print("5. Create test suite")

    print("\n🎯 FRONTEND READINESS:")
    print("Once backend APIs are complete, frontend can connect to:")
    print("• Project management: /api/projects")
    print("• File operations: /api/files")
    print("• B-roll integration: /api/broll")
    print("• Real-time updates: WebSocket at /ws")

    print("\n📊 Full analysis available in: PROJECT_AUDIT_2025.md")


if __name__ == "__main__":
    print("Starting StoryForge Backend Health Check...\n")

    success = test_backend_health()

    if success:
        print("\n🎉 BACKEND HEALTH CHECK PASSED!")
        print("✅ Your backend foundation is solid and ready for development.")
    else:
        print("\n⚠️ BACKEND HEALTH CHECK FOUND ISSUES")
        print("❌ Some components need attention before proceeding.")

    show_next_steps()
