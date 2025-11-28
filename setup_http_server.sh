#!/bin/bash
# Setup script for HTTP MCP Server (for local testing or VPS)

set -e

echo "=========================================="
echo "IDX Stock MCP HTTP Server Setup"
echo "=========================================="

# Get script directory and change to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Configuration
PORT=${MCP_PORT:-8000}
HOST=${MCP_HOST:-127.0.0.1}  # Default to localhost for local use

echo "Project directory: $SCRIPT_DIR"
echo "Port: $PORT"
echo "Host: $HOST"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ℹ️  Running as regular user (local setup)"
    SUDO=""
else
    echo "ℹ️  Running as root (VPS setup)"
    SUDO="sudo"
fi

# 1. Install dependencies
echo "📦 Installing Python dependencies..."

# Try with --break-system-packages if needed
if pip3 install -q -r requirements.txt 2>/dev/null; then
    echo "✅ Dependencies installed"
elif pip3 install --break-system-packages -q -r requirements.txt 2>/dev/null; then
    echo "✅ Dependencies installed (with --break-system-packages)"
else
    echo "⚠️  Warning: Could not install dependencies automatically"
    echo "   Please install manually: pip3 install -r requirements.txt"
    echo "   Or use: pip3 install --break-system-packages -r requirements.txt"
fi
echo ""

# 2. Configure UFW firewall (VPS only, skip for local)
if [ "$EUID" -eq 0 ] && command -v ufw &> /dev/null; then
    echo "🔥 Configuring UFW firewall..."
    # Check if UFW is active
    if $SUDO ufw status | grep -q "Status: active"; then
        echo "UFW is active"
    else
        echo "Enabling UFW..."
        $SUDO ufw --force enable
    fi
    
    # Allow port
    echo "Allowing port $PORT..."
    $SUDO ufw allow $PORT/tcp comment "IDX Stock MCP Server"
    
    # Show status
    echo ""
    echo "UFW Status:"
    $SUDO ufw status | grep -E "(Status|$PORT)" || true
    echo ""
else
    echo "ℹ️  Skipping firewall config (local setup or UFW not available)"
    echo ""
fi

# 3. Test server startup
echo "🧪 Testing server startup..."
timeout 2 python3 -m src.server_http --help 2>&1 | head -5 || {
    echo "⚠️  Server test completed (timeout expected)"
}
echo ""

# 4. Create systemd service (optional, for VPS only)
if [ "$EUID" -eq 0 ]; then
    echo "📝 Creating systemd service file..."
    cat > /tmp/idx-stock-mcp.service << EOF
[Unit]
Description=IDX Stock MCP HTTP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$SCRIPT_DIR
Environment="MCP_HOST=$HOST"
Environment="MCP_PORT=$PORT"
Environment="CACHE_ENABLED=true"
Environment="LOG_LEVEL=INFO"
ExecStart=/usr/bin/python3 -m src.server_http
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    echo "Service file created at /tmp/idx-stock-mcp.service"
    echo "To install as systemd service (VPS only):"
    echo "  sudo cp /tmp/idx-stock-mcp.service /etc/systemd/system/"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable idx-stock-mcp"
    echo "  sudo systemctl start idx-stock-mcp"
    echo ""
else
    echo "ℹ️  Skipping systemd service (running as regular user)"
    echo ""
fi

# 5. Summary
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "To start the server:"
echo "  python3 -m src.server_http"
echo ""
echo "Or with custom port:"
echo "  MCP_PORT=8000 python3 -m src.server_http"
echo ""
echo "Server will be available at:"
echo "  http://$HOST:$PORT"
echo ""
echo "Test endpoints:"
echo "  curl http://localhost:$PORT/health"
echo "  curl http://localhost:$PORT/tools"
echo "  curl http://localhost:$PORT/api/price/BBCA"
echo ""

