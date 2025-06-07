@echo off
REM Genie Whisper X - Windows Launcher Script

echo 🧞 Starting Genie Whisper X...

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python not found. Please install Python 3.11 or higher.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python version check passed: %PYTHON_VERSION%

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install Python dependencies
if exist "requirements.txt" (
    echo 📥 Installing Python dependencies...
    pip install -r requirements.txt
) else (
    echo ⚠️ Warning: requirements.txt not found
)

REM Check if models directory exists
if not exist "models" (
    echo 🤖 Setting up AI models...
    python scripts\setup_models.py
) else (
    echo ✅ Models directory found
)

REM Check if Node.js dependencies are installed
if not exist "node_modules" (
    echo 📦 Installing Node.js dependencies...
    npm install
) else (
    echo ✅ Node.js dependencies found
)

REM Start the application
echo 🚀 Launching Genie Whisper X...
echo    - Backend: Python agent + WebSocket server
echo    - Frontend: Tauri + React UI
echo.
echo Press Ctrl+C to stop

REM Run in development mode
npm run dev

pause