"""
Custom Exceptions for PricePulse application.
"""

class PricePulseException(Exception):
    """Base exception for all PricePulse errors."""
    pass


class ProductNotFoundError(PricePulseException):
    """Raised when a product is not found in the database or search results."""
    pass


class InvalidPriceDataError(PricePulseException):
    """Raised when price input or historical data format is invalid."""
    pass


class APIConnectionError(PricePulseException):
    """Raised when external API or web fetching fails."""
    pass


class ReportGenerationError(PricePulseException):
    """Raised when report or graph generation fails."""
    pass
