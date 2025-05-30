import uvicorn
from dotenv import load_dotenv
from utils.logger import setup_logger
from utils.uvicorn_logger import uvicorn_logger

logger = setup_logger(__name__)

load_dotenv()

if __name__ == "__main__":
    logger.info("Uvicorn started...")
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True, log_config=uvicorn_logger())
