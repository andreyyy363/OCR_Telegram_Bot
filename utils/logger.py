"""
Logger configuration for the OCR Telegram Bot.
"""
import os
import logging
from logging.handlers import RotatingFileHandler

from consts import (
    LOG_DIR_NAME, LOG_FILE_NAME, LOG_FORMAT, LOG_LEVEL,
    LOG_MAX_BYTES, LOG_BACKUP_COUNT, LOG_ENCODING
)


def setup_logger() -> logging.Logger:
    """
    Configure and return the application logger.

    Sets up both console and rotating file handlers with the configured
    format, level, and rotation settings.

    :return: Configured logger instance
    """
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), LOG_DIR_NAME)
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, LOG_FILE_NAME)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL))

    # Avoid adding handlers multiple times
    if root_logger.handlers:
        return logging.getLogger(__name__)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL))
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding=LOG_ENCODING
    )
    file_handler.setLevel(getattr(logging, LOG_LEVEL))
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    return logging.getLogger(__name__)
