"""
Trading Presentation Layer - API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.application.dependencies import get_trading_application_service
from app.application.trading.services import TradingApplicationService
from app.schemas.user import (
    StockOrderRequest, StockOrderResponse, UserPortfolio, UserStockOrder
)
from app.core.security import get_current_user
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trading", tags=["trading"])


@router.post("/orders", response_model=StockOrderResponse)
async def place_order(
    request: StockOrderRequest,
    current_user: dict = Depends(get_current_user),
    trading_service: TradingApplicationService = Depends(get_trading_application_service)
):
    """下單"""
    try:
        result = await trading_service.place_order(
            user_id=current_user["user_id"],
            symbol=request.symbol,
            order_type=request.order_type,
            quantity=request.quantity,
            price=request.price
        )
        
        if result["success"]:
            return StockOrderResponse(
                success=True,
                message=result["message"],
                order_id=result["order"]["id"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except Exception as e:
        logger.error(f"Place order error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="下單失敗"
        )


@router.delete("/orders/{order_id}")
async def cancel_order(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    trading_service: TradingApplicationService = Depends(get_trading_application_service)
):
    """取消訂單"""
    try:
        result = await trading_service.cancel_order(
            order_id=order_id,
            user_id=current_user["user_id"]
        )
        
        if result["success"]:
            return {"success": True, "message": result["message"]}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except Exception as e:
        logger.error(f"Cancel order error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取消訂單失敗"
        )


@router.get("/portfolio", response_model=UserPortfolio)
async def get_portfolio(
    current_user: dict = Depends(get_current_user),
    trading_service: TradingApplicationService = Depends(get_trading_application_service)
):
    """獲取投資組合"""
    try:
        result = await trading_service.get_user_portfolio(current_user["user_id"])
        
        if result["success"]:
            return UserPortfolio(
                success=True,
                portfolio=result["portfolio"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except Exception as e:
        logger.error(f"Get portfolio error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取投資組合失敗"
        )


@router.get("/orders", response_model=List[UserStockOrder])
async def get_user_orders(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    trading_service: TradingApplicationService = Depends(get_trading_application_service)
):
    """獲取使用者訂單"""
    try:
        result = await trading_service.get_user_orders(
            user_id=current_user["user_id"],
            skip=skip,
            limit=limit
        )
        
        if result["success"]:
            return [
                UserStockOrder(
                    id=order["id"],
                    symbol=order["symbol"],
                    order_type=order["order_type"],
                    quantity=order["quantity"],
                    price=order["price"],
                    filled_quantity=order["filled_quantity"],
                    remaining_quantity=order["remaining_quantity"],
                    status=order["status"],
                    created_at=order["created_at"]
                )
                for order in result["orders"]
            ]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except Exception as e:
        logger.error(f"Get user orders error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取訂單失敗"
        )


@router.get("/stocks/{symbol}/orderbook")
async def get_order_book(
    symbol: str,
    trading_service: TradingApplicationService = Depends(get_trading_application_service)
):
    """獲取訂單簿"""
    try:
        result = await trading_service.get_order_book(symbol)
        
        if result["success"]:
            return result["order_book"]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except Exception as e:
        logger.error(f"Get order book error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取訂單簿失敗"
        )


@router.get("/stocks")
async def get_all_stocks(
    trading_service: TradingApplicationService = Depends(get_trading_application_service)
):
    """獲取所有股票"""
    try:
        result = await trading_service.get_all_stocks()
        
        if result["success"]:
            return result["stocks"]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except Exception as e:
        logger.error(f"Get all stocks error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取股票列表失敗"
        )


@router.get("/stocks/{symbol}")
async def get_stock_info(
    symbol: str,
    trading_service: TradingApplicationService = Depends(get_trading_application_service)
):
    """獲取股票資訊"""
    try:
        result = await trading_service.get_stock_info(symbol)
        
        if result["success"]:
            return result["stock"]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except Exception as e:
        logger.error(f"Get stock info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取股票資訊失敗"
        )