"""HTTP/SSE MCP Server for remote access via network.

Note: This HTTP server is for local testing or VPS deployment.
For Claude Desktop integration, use src.server.py instead (stdio-based MCP).

To run:
    python3 -m src.server_http
    
Or use the start script:
    ./start_http_server.sh
"""

import asyncio
import json
import logging
import sys
from typing import Any
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import MCP server components
from mcp.server import Server
from mcp.types import Tool, TextContent

# Import all tools
from src.tools.price import get_stock_price_tool, get_stock_price
from src.tools.info import get_stock_info_tool, get_stock_info
from src.tools.historical import get_historical_data_tool, get_historical_data
from src.tools.indicators import get_technical_indicators_tool, get_technical_indicators
from src.tools.search import get_search_stocks_tool, search_stocks
from src.tools.market import get_market_summary_tool, get_market_summary
from src.tools.compare import get_compare_stocks_tool, compare_stocks
from src.tools.watchlist import get_watchlist_prices_tool, get_watchlist_prices
from src.tools.financial_ratios import get_financial_ratios_tool, get_financial_ratios
from src.tools.volume_analysis import get_volume_analysis_tool, get_volume_analysis
from src.tools.volatility_analysis import get_volatility_analysis_tool, get_volatility_analysis
from src.config.settings import settings
from src.utils.exceptions import MCPToolError

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="IDX Stock MCP Server",
    description="MCP Server for Indonesian Stock Market Data",
    version="0.1.0"
)

# Enable CORS for remote clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create MCP server instance
mcp_server = Server("idx-stock-mcp")


@mcp_server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        get_stock_price_tool(),
        get_stock_info_tool(),
        get_historical_data_tool(),
        get_technical_indicators_tool(),
        get_search_stocks_tool(),
        get_market_summary_tool(),
        get_compare_stocks_tool(),
        get_watchlist_prices_tool(),
        get_financial_ratios_tool(),
        get_volume_analysis_tool(),
        get_volatility_analysis_tool(),
    ]


@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        logger.info(f"Tool called: {name} with arguments: {arguments}")

        # Route to appropriate tool handler
        tool_handlers = {
            "get_stock_price": get_stock_price,
            "get_stock_info": get_stock_info,
            "get_historical_data": get_historical_data,
            "get_technical_indicators": get_technical_indicators,
            "search_stocks": search_stocks,
            "get_market_summary": get_market_summary,
            "compare_stocks": compare_stocks,
            "get_watchlist_prices": get_watchlist_prices,
            "get_financial_ratios": get_financial_ratios,
            "get_volume_analysis": get_volume_analysis,
            "get_volatility_analysis": get_volatility_analysis,
        }

        handler = tool_handlers.get(name)
        if not handler:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": True,
                    "code": "INVALID_PARAMETER",
                    "message": f"Unknown tool: {name}",
                }, indent=2)
            )]

        result = await handler(arguments)
        logger.info(f"Tool {name} completed successfully")

        # Check if result contains error (legacy support for tools that return error dicts)
        if isinstance(result, dict) and result.get("error"):
            # Return error as-is
            result_text = json.dumps(result, indent=2, ensure_ascii=False)
            return [TextContent(type="text", text=result_text)]

        # Format result as JSON string
        result_text = json.dumps(result, indent=2, ensure_ascii=False) if isinstance(result, dict) else str(result)

        return [TextContent(type="text", text=result_text)]

    except MCPToolError as e:
        # Handle MCP tool exceptions properly
        logger.error(f"Tool error in {name}: {e.code} - {e.message}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": True,
                "code": e.code,
                "message": e.message,
                "suggestion": e.suggestion,
            }, indent=2, ensure_ascii=False)
        )]
    except Exception as e:
        logger.error(f"Error handling tool {name}: {str(e)}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": True,
                "code": "NETWORK_ERROR",
                "message": f"Internal error: {str(e)}",
                "suggestion": "Coba lagi nanti atau periksa log untuk detail"
            }, indent=2, ensure_ascii=False)
        )]


# HTTP API Endpoints

@app.get("/")
async def root():
    """Root endpoint with server info."""
    return {
        "name": "IDX Stock MCP Server",
        "version": "0.1.0",
        "status": "running",
        "tools": 8
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/tools")
async def list_tools():
    """List all available MCP tools."""
    try:
        tools = await handle_list_tools()
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in tools
            ]
        }
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/mcp/call")
async def call_tool(request: Request):
    """Call an MCP tool via HTTP POST."""
    try:
        body = await request.json()
        tool_name = body.get("tool")
        arguments = body.get("arguments", {})
        
        if not tool_name:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing 'tool' parameter"}
            )
        
        logger.info(f"HTTP call to tool: {tool_name}")
        result = await handle_call_tool(tool_name, arguments)
        
        # Extract text content from result
        if result and len(result) > 0:
            content = result[0].text if hasattr(result[0], 'text') else str(result[0])
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"result": content}
        else:
            return {"result": None}
            
    except Exception as e:
        logger.error(f"Error in HTTP tool call: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/mcp/batch")
async def batch_call_tools(request: Request):
    """Call multiple MCP tools in batch."""
    try:
        body = await request.json()
        calls = body.get("calls", [])
        
        results = []
        for call in calls:
            tool_name = call.get("tool")
            arguments = call.get("arguments", {})
            
            if tool_name:
                result = await handle_call_tool(tool_name, arguments)
                if result and len(result) > 0:
                    content = result[0].text if hasattr(result[0], 'text') else str(result[0])
                    try:
                        results.append(json.loads(content))
                    except json.JSONDecodeError:
                        results.append({"result": content})
                else:
                    results.append({"result": None})
            else:
                results.append({"error": "Missing tool name"})
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Error in batch call: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# Convenience endpoints for common operations

@app.get("/api/price/{ticker}")
async def get_price(ticker: str):
    """Get stock price via REST API."""
    try:
        result = await get_stock_price({"ticker": ticker})
        return result
    except MCPToolError as e:
        return JSONResponse(
            status_code=400,
            content={
                "error": True,
                "code": e.code,
                "message": e.message,
                "suggestion": e.suggestion,
            }
        )
    except Exception as e:
        logger.error(f"Error in /api/price/{ticker}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/info/{ticker}")
async def get_info(ticker: str):
    """Get stock info via REST API."""
    try:
        result = await get_stock_info({"ticker": ticker})
        # Handle legacy error dict format
        if isinstance(result, dict) and result.get("error"):
            return JSONResponse(status_code=400, content=result)
        return result
    except MCPToolError as e:
        return JSONResponse(
            status_code=400,
            content={
                "error": True,
                "code": e.code,
                "message": e.message,
                "suggestion": e.suggestion,
            }
        )
    except Exception as e:
        logger.error(f"Error in /api/info/{ticker}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/market")
async def get_market():
    """Get market summary via REST API."""
    try:
        result = await get_market_summary({})
        return result
    except Exception as e:
        logger.error(f"Error in /api/market: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


def main():
    """Main entry point for HTTP server."""
    import os
    
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))
    
    logger.info(f"Starting IDX Stock MCP HTTP Server on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=settings.LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    main()

