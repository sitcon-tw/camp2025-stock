from contextlib import asynccontextmanager
from os import environ

from dotenv import load_dotenv
from fastapi import FastAPI

from api.routes import webhook, broadcast, health
from bot.setup import initialize
from utils.logger import setup_logger

load_dotenv()

logger = setup_logger(__name__)
WEBHOOK_SECRET = environ.get("WEBHOOK_SECRET")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server started.")
    await initialize()
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET was not set!")
    yield
    logger.info("Server stopped.")

server = FastAPI(lifespan=lifespan)

# Include routers
server.include_router(webhook.router)
server.include_router(broadcast.router)
server.include_router(health.router)
