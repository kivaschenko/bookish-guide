#!/bin/bash
# Startup script for the legacy web interface
# This script ensures the server runs from the correct directory

echo "🎬 Starting StoryForge Legacy Web Interface..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Use port 8080 by default, or allow override with first argument
PORT=${1:-8080}

echo "📁 Project root: $PROJECT_ROOT"
echo "🌐 Web interface will be available at: http://localhost:$PORT"

# Check if broll_timing.json exists
if [ ! -f "$PROJECT_ROOT/temp/broll_timing.json" ]; then
    echo "⚠️  Warning: broll_timing.json not found at $PROJECT_ROOT/temp/"
    echo "   Make sure to run your video generation first to create timeline data."
    echo ""
fi

# Change to project root and run the server
cd "$PROJECT_ROOT"
echo "🚀 Starting server from: $(pwd)"

# Try to activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Create a simple Python script to start the server with custom port
cat > /tmp/start_legacy_server.py << EOF
#!/usr/bin/env python3
import sys
sys.path.append('backend/legacy_server')
from server import start_premontage_server

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    start_premontage_server(port=port)
EOF

# Use python3 if python is not available
if command -v python >/dev/null 2>&1; then
    python /tmp/start_legacy_server.py "$PORT"
elif command -v python3 >/dev/null 2>&1; then
    python3 /tmp/start_legacy_server.py "$PORT"
else
    echo "❌ Error: Neither python nor python3 found in PATH"
    exit 1
fi