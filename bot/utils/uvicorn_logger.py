import os

from utils.logger import loggingFormatter
from dotenv import load_dotenv

load_dotenv()
DEBUG = os.getenv("DEBUG", "False").lower() in ("1", "true", "yes")

def uvicorn_logger():
    return {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "uvicorn_style": {
                "()": loggingFormatter,
            },
        },
        "handlers": {
            "default": {
                "formatter": "uvicorn_style",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": "DEBUG" if DEBUG else "INFO",
            "handlers": ["default"],
        },
        "loggers": {
            "uvicorn": {
                "level": "DEBUG" if DEBUG else "INFO",
                "handlers": ["default"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "DEBUG" if DEBUG else "INFO",
                "handlers": ["default"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "DEBUG" if DEBUG else "INFO",
                "handlers": ["default"],
                "propagate": False,
            },
        }
    }
