"""Logging utilities for Deep Agents v2"""

import logging
import sys
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console

console = Console()


def setup_logger(
    name: str = "deep_agents",
    level: str = "INFO"
) -> logging.Logger:
    """
    Set up a logger with rich formatting

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Add rich handler
    handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        markup=True
    )
    handler.setFormatter(
        logging.Formatter(
            "%(message)s",
            datefmt="[%X]"
        )
    )
    logger.addHandler(handler)

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance

    Args:
        name: Logger name (defaults to 'deep_agents')

    Returns:
        Logger instance
    """
    return logging.getLogger(name or "deep_agents")
