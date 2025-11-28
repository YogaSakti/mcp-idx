#!/bin/bash
# Start HTTP MCP Server (for local testing)

# Get script directory and change to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Configuration
PORT=${MCP_PORT:-8000}
HOST=${MCP_HOST:-127.0.0.1}  # Default to localhost for local use

echo "Starting IDX Stock MCP HTTP Server..."
echo "Host: $HOST"
echo "Port: $PORT"
echo ""

# Check if we're in venv, if not try to activate it
if [ -z "$VIRTUAL_ENV" ] && [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if FastAPI is installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "⚠️  FastAPI not found. Installing dependencies..."
    pip install fastapi uvicorn[standard] || {
        echo "❌ Failed to install dependencies"
        echo "   Please run: pip install fastapi uvicorn[standard]"
        exit 1
    }
fi

# Check if port is already in use
if command -v lsof >/dev/null 2>&1 && lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Warning: Port $PORT is already in use"
    echo "   Kill existing process or use different port: MCP_PORT=8001 $0"
    exit 1
fi

# Start server
python3 -m src.server_http

