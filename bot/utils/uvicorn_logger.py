from utils.logger import loggingFormatter

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
            "level": "INFO",
            "handlers": ["default"],
        },
        "loggers": {
            "uvicorn": {
                "level": "INFO",
                "handlers": ["default"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["default"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["default"],
                "propagate": False,
            },
        }
    }
