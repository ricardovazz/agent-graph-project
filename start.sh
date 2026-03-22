#!/bin/bash
# Start the Agent Graph Dashboard

echo "=============================================="
echo "  Agent Graph Dashboard - Startup Script"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -e . -q

# Check if Node modules exist
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Set environment variable reminder
echo ""
echo "=============================================="
echo "  IMPORTANT: Set your API key before running"
echo "=============================================="
echo "  export OPENROUTER_API_KEY=your_key_here"
echo ""

# Start the server
echo "Starting FastAPI server on http://localhost:8000..."
python -m uvicorn src.server:app_api --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Start the frontend
echo "Starting frontend dev server..."
cd frontend
npm run dev
cd ..

# Wait for processes
wait $SERVER_PID
