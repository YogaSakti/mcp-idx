"""Custom exceptions for MCP tools."""


class MCPToolError(Exception):
    """Base exception for MCP tool errors."""
    def __init__(self, code: str, message: str, suggestion: str = None):
        self.code = code
        self.message = message
        self.suggestion = suggestion
        super().__init__(self.message)


class InvalidTickerError(MCPToolError):
    """Raised when ticker is invalid."""
    def __init__(self, ticker: str, suggestion: str = None):
        super().__init__(
            code="INVALID_TICKER",
            message=f"Ticker '{ticker}' tidak valid atau tidak ditemukan",
            suggestion=suggestion or "Gunakan tool search_stocks untuk mencari ticker yang valid"
        )


class DataUnavailableError(MCPToolError):
    """Raised when data is unavailable."""
    def __init__(self, message: str, suggestion: str = None):
        super().__init__(
            code="DATA_UNAVAILABLE",
            message=message,
            suggestion=suggestion or "Pastikan ticker valid dan coba lagi"
        )


class NetworkError(MCPToolError):
    """Raised when there's a network error."""
    def __init__(self, message: str):
        super().__init__(
            code="NETWORK_ERROR",
            message=message,
            suggestion="Coba lagi nanti atau periksa koneksi internet"
        )


class InvalidParameterError(MCPToolError):
    """Raised when parameters are invalid."""
    def __init__(self, message: str):
        super().__init__(
            code="INVALID_PARAMETER",
            message=message,
            suggestion="Periksa parameter yang dikirim"
        )

