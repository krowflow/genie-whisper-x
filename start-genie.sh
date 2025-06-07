#!/bin/bash
# Genie Whisper X - Linux/WSL Launcher Script

set -e

echo "🧞 Starting Genie Whisper X..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d" " -f2 | cut -d"." -f1,2)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python $REQUIRED_VERSION or higher required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python version check passed: $PYTHON_VERSION"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    echo "📥 Installing Python dependencies..."
    pip install -r requirements.txt
else
    echo "⚠️ Warning: requirements.txt not found"
fi

# Check if models directory exists
if [ ! -d "models" ]; then
    echo "🤖 Setting up AI models..."
    python scripts/setup_models.py
else
    echo "✅ Models directory found"
fi

# Check if Node.js dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
else
    echo "✅ Node.js dependencies found"
fi

# Start the application
echo "🚀 Launching Genie Whisper X..."
echo "   - Backend: Python agent + WebSocket server"
echo "   - Frontend: Tauri + React UI"
echo ""
echo "Press Ctrl+C to stop"

# Run in development mode
npm run dev