from __future__ import annotations

import json
import logging
import sys
from typing import Any

from .config import get_settings

_LOGGER_CACHE: dict[str, logging.Logger] = {}


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "time": self.formatTime(record, self.datefmt),
        }

        if record.exc_info:
            log_entry["exc_info"] = self.formatException(record.exc_info)

        # Fields to exclude to avoid conflicts
        excluded_fields = {
            "msg", "args", "levelname", "levelno", "name",
            "message", "level", "time", "logger", "exc_info",
            "exc_text", "stack_info"  # These are handled above
        }
        
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in log_entry or key in excluded_fields:
                continue
            try:
                json.dumps(value)
                log_entry[key] = value
            except TypeError:
                log_entry[key] = repr(value)

        return json.dumps(log_entry, ensure_ascii=False)


def configure_root_logger() -> None:
    """Configure the root logger once."""
    if logging.getLogger().handlers:
        return

    settings = get_settings()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    logging.basicConfig(
        handlers=[handler],
        level=settings.log_level.upper(),
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a cached logger instance."""
    if name not in _LOGGER_CACHE:
        configure_root_logger()
        _LOGGER_CACHE[name] = logging.getLogger(name)
    return _LOGGER_CACHE[name]
