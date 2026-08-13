"""
Logging Configuration for PricePulse.
"""

import logging
import os
from pathlib import Path

def setup_logger(name: str = "PricePulse", log_file: str = "logs/pricepulse.log", level=logging.INFO) -> logging.Logger:
    """Configures and returns a logger instance writing to both console and log file."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Formatters
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # File Handler
    try:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    except Exception as e:
        console_handler.emit(logging.LogRecord(
            name=name, level=logging.WARNING, pathname="", lineno=0,
            msg=f"Could not create file log handler: {e}", args=(), exc_info=None
        ))

    return logger
