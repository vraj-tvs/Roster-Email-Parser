import logging
import os

LOG_DIR = "data/logs"
LOG_FILE = os.path.join(LOG_DIR, "pipeline.log")


def init_logger():
    """
    Initializes and returns a logger that writes to a log file.
    """
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    logger = logging.getLogger("RosterEmailLogger")
    logger.setLevel(logging.INFO)
    # Avoid duplicate handlers if called multiple times
    if not logger.handlers:
        file_handler = logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
