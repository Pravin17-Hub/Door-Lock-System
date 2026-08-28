"""
FaceSecure - Logger Utility
Configures application-wide logging to both console and rotating log files.
"""

import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logger(name: str = "FaceSecure") -> logging.Logger:
    """Creates and configures a rotating file and console logger."""
    os.makedirs("data/logs", exist_ok=True)
    log_file = os.path.join("data", "logs", "facesecure.log")

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if logger.hasHandlers():
        return logger

    # Formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # File Handler (5 MB max, 3 backups)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
