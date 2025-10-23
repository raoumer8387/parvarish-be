"""Logging configuration (placeholder).

Set up application-wide logging formatters, handlers, and levels.
"""

import logging


def get_logger(name: str = "parvarish") -> logging.Logger:
    """Return a configured logger (placeholder)."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    return logger
