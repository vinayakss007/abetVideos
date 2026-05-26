#!/bin/bash
# Run script for Abet Videos backend
set -e

echo "=== Abet Videos - AI Video Generator ==="

# Set Python version
echo "Setting Python 3.11..."
pyenv local 3.11.15

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi
source venv/bin/activate

# Install dependencies
echo "Installing backend dependencies..."
pip install -e "backend/[dev]" --quiet

# Install FFmpeg if not available
if ! command -v ffmpeg &> /dev/null; then
    echo "Installing FFmpeg..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y ffmpeg
    elif command -v yum &> /dev/null; then
        sudo yum install -y ffmpeg || echo "FFmpeg not in yum repos, install manually"
    else
        echo "Please install FFmpeg manually"
    fi
fi

# Check for .env file
if [ ! -f "backend/.env" ]; then
    echo ""
    echo "WARNING: No backend/.env file found."
    echo "Copy backend/.env.example to backend/.env and fill in your API keys."
    echo ""
fi

# Create output directory
mkdir -p output

# Start the server
echo ""
echo "Starting Abet Videos backend server..."
echo "API docs: http://localhost:8000/docs"
echo ""
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir backend
