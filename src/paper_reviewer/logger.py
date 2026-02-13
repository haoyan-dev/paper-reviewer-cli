"""Logging configuration for paper reviewer CLI."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(log_level: str = "INFO", log_file: Optional[Path] = None) -> None:
    """
    Configure Python logging module for the application.

    Sets up:
    - Console handler (INFO level and above)
    - Optional file handler (DEBUG level and above)

    Args:
        log_level: Logging level for console output (default: "INFO")
        log_file: Optional path to log file. If None, uses default location.
                  If provided, creates parent directories if needed.
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Determine log file path
    if log_file is None:
        # Default: logs/paper-reviewer.log in project root
        project_root = Path(__file__).parent.parent.parent
        log_dir = project_root / "logs"
        log_file = log_dir / "paper-reviewer.log"
    else:
        log_dir = log_file.parent

    # Create log directory if it doesn't exist
    if log_dir and not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to lowest level, handlers filter

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler (INFO level and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (DEBUG level and above)
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        # If we can't create log file, just log to console
        root_logger.warning(f"Could not create log file {log_file}: {e}. Logging to console only.")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name, typically __name__ of the calling module

    Returns:
        Logger instance configured with application settings
    """
    return logging.getLogger(name)
