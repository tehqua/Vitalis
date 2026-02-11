"""Base class for agent tools."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BaseTool:
    """Base class for all agent tools."""

    def __init__(self, name: str, description: str):
        """
        Initialize the base tool.

        Args:
            name: Tool name identifier
            description: Human-readable tool description
        """
        self.name = name
        self.description = description

    def format_error(self, error: Exception) -> str:
        """
        Format error message for LLM consumption.

        Args:
            error: Exception that occurred

        Returns:
            Formatted error message
        """
        logger.error(f"Tool {self.name} error: {str(error)}")
        return f"Error: Unable to retrieve information. {str(error)}"

    def truncate_text(self, text: str, max_length: int = 2000) -> str:
        """
        Truncate text to fit within LLM context window.

        Args:
            text: Text to truncate
            max_length: Maximum allowed length

        Returns:
            Truncated text with indicator if truncated
        """
        if len(text) <= max_length:
            return text
        truncated_chars = len(text) - max_length
        return text[:max_length] + f"\n\n... (truncated {truncated_chars} characters)"
