"""Logging configuration for the application."""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime


def setup_logging(log_dir: Path, model_name: str) -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        log_dir: Directory to store log files
        model_name: Name of the model being used (for log file naming)

    Returns:
        Configured logger instance
    """
    log_dir = log_dir / model_name
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    logger.handlers.clear()

    # Log file naming: model_name_YYYYMMDD_HHMMSS.log
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{model_name}_{timestamp}.log"

    # File handler (DEBUG level)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # Console handler (INFO level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialized for model: {model_name}")
    logger.info(f"Log file: {log_file}")

    return logger
