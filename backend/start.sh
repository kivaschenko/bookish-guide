#!/bin/bash
# Simple startup script for the Premontage FastAPI server

echo "🎬 Starting StoryForge Premontage FastAPI Server..."

# Check if we're in the backend directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from the backend directory."
    exit 1
fi

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
elif [ -d "../venv" ]; then
    echo "📦 Activating virtual environment..."
    source ../venv/bin/activate
fi

# Install dependencies if requirements.txt is newer than last install
if [ ! -f ".requirements_installed" ] || [ "requirements.txt" -nt ".requirements_installed" ]; then
    echo "📋 Installing/updating dependencies..."
    pip install -r requirements.txt
    touch .requirements_installed
fi

# Start the server
echo "🚀 Starting server..."
python run.py "$@"