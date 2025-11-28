# Local Setup Guide

This guide explains how to run the IDX Stock MCP Server locally on your machine.

## Prerequisites

1. **Python 3.11+** installed
2. **Claude Desktop** installed
3. **Dependencies** installed (see below)

## Step 1: Install Dependencies

On your local machine:

```bash
cd /path/to/mpc-idx

# Option 1: Using virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Option 2: System-wide
pip install -r requirements.txt
```

## Step 2: Test the Server

Verify the server works:

```bash
# Test imports
python3 -c "from src.server import server; print('OK')"

# Test server startup (will wait for stdio input)
python3 -m src.server
```

Press Ctrl+C to stop.

## Step 3: Configure Claude Desktop

### Find Config File Location

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Add Configuration

Open `claude_desktop_config.json` and add:

```json
{
  "mcpServers": {
    "idx-stocks": {
      "command": "python3",
      "args": ["-m", "src"],
      "cwd": "/path/to/mpc-idx",
      "env": {
        "CACHE_ENABLED": "true",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Important:** Replace `/path/to/mpc-idx` with the actual path to your project directory.

### Example Configurations

#### macOS
```json
{
  "mcpServers": {
    "idx-stocks": {
      "command": "python3",
      "args": ["-m", "src"],
      "cwd": "/Users/yourusername/mcp-idx",
      "env": {
        "CACHE_ENABLED": "true",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### Windows
```json
{
  "mcpServers": {
    "idx-stocks": {
      "command": "python",
      "args": ["-m", "src"],
      "cwd": "C:\\Users\\YourUsername\\mcp-idx",
      "env": {
        "CACHE_ENABLED": "true",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### Linux
```json
{
  "mcpServers": {
    "idx-stocks": {
      "command": "python3",
      "args": ["-m", "src"],
      "cwd": "/home/yourusername/mcp-idx",
      "env": {
        "CACHE_ENABLED": "true",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Using Virtual Environment

If using a venv, point to the venv's Python:

**macOS/Linux:**
```json
{
  "mcpServers": {
    "idx-stocks": {
      "command": "/path/to/mpc-idx/venv/bin/python",
      "args": ["-m", "src"],
      "cwd": "/path/to/mpc-idx"
    }
  }
}
```

**Windows:**
```json
{
  "mcpServers": {
    "idx-stocks": {
      "command": "C:\\path\\to\\mpc-idx\\venv\\Scripts\\python.exe",
      "args": ["-m", "src"],
      "cwd": "C:\\path\\to\\mpc-idx"
    }
  }
}
```

## Step 4: Restart Claude Desktop

1. **Quit Claude Desktop completely** (not just minimize)
2. **Reopen Claude Desktop**
3. The MCP server should start automatically

## Step 5: Verify Connection

1. **Check Claude Desktop Logs** for any errors
2. **Test in Claude Chat:**
   - "What tools do you have available?"
   - "Get the current price of BBCA stock"

## Troubleshooting

### Server Won't Start

**Check Python path:**
```bash
which python3  # macOS/Linux
where python   # Windows
```

**Test server manually:**
```bash
cd /path/to/mpc-idx
python3 -m src.server
```

Should start without errors (will wait for stdio input).

### Import Errors

**Check dependencies:**
```bash
python3 -c "import mcp; import yfinance; print('OK')"
```

If missing, install:
```bash
pip install -r requirements.txt
```

### Path Issues

- Use **absolute paths** for `cwd`, not relative
- On Windows, use forward slashes or double backslashes: `C:\\path\\to\\project`
- Ensure `cwd` points to project root (where `src/` folder is)

### Permission Errors

- Ensure Python executable has execute permissions
- Check file permissions on project directory
- On macOS, may need to grant Terminal/Claude Desktop permissions

## Testing

Once connected, try these in Claude:

1. "What's the current price of BBCA?"
2. "Tell me about BBRI stock"
3. "Search for banking stocks"
4. "What's the IHSG status today?"
5. "Compare BBCA, BBRI, and BMRI performance"

## Available Tools

Once connected, Claude will have access to 8 tools:

1. `get_stock_price` - Get current stock price
2. `get_stock_info` - Get company information
3. `get_historical_data` - Get OHLCV historical data
4. `get_technical_indicators` - Calculate technical indicators
5. `search_stocks` - Search for stocks
6. `get_market_summary` - Get IHSG and market summary
7. `compare_stocks` - Compare multiple stocks
8. `get_watchlist_prices` - Get prices for multiple stocks

## Quick Reference

**Start server manually:**
```bash
cd /path/to/mpc-idx
python3 -m src.server
```

**Check logs:**
```bash
tail -f idx-stock-mcp.log
```

**Test imports:**
```bash
python3 -c "from src.tools.price import get_stock_price_tool; print('OK')"
```

