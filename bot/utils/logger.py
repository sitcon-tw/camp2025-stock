import logging
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()
DEBUG = bool(os.environ.get("DEBUG", False))


class loggingFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[41m",  # Red background
        "TIME": "\033[34m",  # Blue
        "RESET": "\033[0m",
    }

    def format(self, record):
        levelname = record.levelname
        level = f"{levelname}:"
        if len(level) < 9:
            level = level.ljust(9)

        if sys.stderr.isatty():
            color = self.COLORS.get(levelname, "")
            reset = self.COLORS["RESET"]
            level = f"{color}{level}{reset}"

        now = datetime.now().strftime("%m:%d %H:%M:%S")

        return f"{level} {self.COLORS["TIME"]}{now}{self.COLORS["RESET"]} [{record.name}] {record.getMessage()}"


def setup_logger(name: str = None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(loggingFormatter())
        logger.addHandler(handler)

    return logger
