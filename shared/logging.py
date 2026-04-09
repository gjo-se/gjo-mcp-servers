"""Zentrales Logging-Setup für alle MCP-Server."""

import logging
import sys

from shared.config import settings


def configure_logging() -> None:
    """Konfiguriert das Root-Logger-Setup für alle Server."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Gibt einen benannten Logger zurück."""
    return logging.getLogger(name)
