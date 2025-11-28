"""MCP Server for IDX Stock Data."""

import asyncio
import json
import logging
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import all tools
from src.tools.price import get_stock_price_tool, get_stock_price
from src.tools.info import get_stock_info_tool, get_stock_info
from src.tools.historical import get_historical_data_tool, get_historical_data
from src.tools.indicators import get_technical_indicators_tool, get_technical_indicators
from src.tools.fibonacci import get_fibonacci_levels_tool, get_fibonacci_levels
from src.tools.ma_crossover import get_ma_crossover_tool, get_ma_crossovers
from src.tools.search import get_search_stocks_tool, search_stocks
from src.tools.market import get_market_summary_tool, get_market_summary
from src.tools.compare import get_compare_stocks_tool, compare_stocks
from src.tools.watchlist import get_watchlist_prices_tool, get_watchlist_prices
from src.config.settings import settings

# Configure logging
# Use stderr for console output to avoid interfering with JSON-RPC on stdout
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler(sys.stderr),  # Use stderr instead of stdout
    ],
)

logger = logging.getLogger(__name__)

# Create MCP server
server = Server("idx-stock-mcp")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        get_stock_price_tool(),
        get_stock_info_tool(),
        get_historical_data_tool(),
        get_technical_indicators_tool(),
        get_fibonacci_levels_tool(),
        get_ma_crossover_tool(),
        get_search_stocks_tool(),
        get_market_summary_tool(),
        get_compare_stocks_tool(),
        get_watchlist_prices_tool(),
    ]


@server.call_tool()
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
            "get_fibonacci_levels": get_fibonacci_levels,
            "get_ma_crossovers": get_ma_crossovers,
            "search_stocks": search_stocks,
            "get_market_summary": get_market_summary,
            "compare_stocks": compare_stocks,
            "get_watchlist_prices": get_watchlist_prices,
        }

        handler = tool_handlers.get(name)
        if not handler:
            from src.utils.exceptions import InvalidParameterError
            raise InvalidParameterError(f"Unknown tool: {name}")

        result = await handler(arguments)
        logger.info(f"Tool {name} completed successfully")

        # Check if result contains error (legacy support for tools that still return errors)
        if isinstance(result, dict) and result.get("error"):
            # Convert legacy error format to exception
            from src.utils.exceptions import MCPToolError
            code = result.get("code", "UNKNOWN_ERROR")
            message = result.get("message", "An error occurred")
            suggestion = result.get("suggestion")
            raise MCPToolError(code=code, message=message, suggestion=suggestion)

        # Format result as JSON string
        result_text = json.dumps(result, indent=2, ensure_ascii=False) if isinstance(result, dict) else str(result)

        return [TextContent(type="text", text=result_text)]

    except Exception as e:
        # Let MCP SDK handle the exception properly
        logger.error(f"Error handling tool {name}: {str(e)}", exc_info=True)
        raise


async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting IDX Stock MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())

