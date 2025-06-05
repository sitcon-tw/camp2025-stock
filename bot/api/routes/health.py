from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from bot.instance import bot
from utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

@router.get("/healthz")
async def healthz():
    try:
        await bot.bot.get_me()
        logger.info("Healthz endpoint checked successfully.")
        return JSONResponse(status_code=status.HTTP_200_OK, content={"ok": True})
    except Exception as e:
        logger.error(f"Error checking healthz: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"ok": False})
