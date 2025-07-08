from fastapi import APIRouter, Depends, HTTPException, status
from app.services.user_service import UserService, get_user_service
from app.schemas.user import (
    UserRegistrationRequest, UserRegistrationResponse,
    UserLoginRequest, UserLoginResponse, UserPortfolio,
    StockOrderRequest, StockOrderResponse,
    TransferRequest, TransferResponse,
    UserPointLog, UserStockOrder
)
from app.schemas.public import QRCodeRedeemRequest, QRCodeRedeemResponse
from app.core.security import get_current_user
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ========== 使用者認證 ==========
# 已改為BOT代理