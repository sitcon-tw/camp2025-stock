from os import environ

import uvicorn
from dotenv import load_dotenv

from utils.logger import setup_logger
from utils.uvicorn_logger import uvicorn_logger

logger = setup_logger("entrypoint")

load_dotenv()
PORT = int(environ.get("PORT", 8000))
DEBUG = environ.get("DEBUG", "False").lower() in ("1", "true", "yes")
ENVIRONMENT = environ.get("ENVIRONMENT", "production") == "development"

if __name__ == "__main__":
    logger.info("Uvicorn started...")
    if DEBUG:
        logger.debug("Debug mode is on")
    else:
        logger.info("Debug mode is off")
    if ENVIRONMENT:
        logger.info("Development mode is on, auto reload is enabled")
    else:
        logger.info("Development mode is off, auto reload is not enabled")
    uvicorn.run("api.app:server", host="0.0.0.0", port=PORT, reload=ENVIRONMENT, log_config=uvicorn_logger())
