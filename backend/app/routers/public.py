from fastapi import APIRouter, Depends, Query
from app.services.public_service import PublicService, get_public_service
from app.schemas.public import (
    PriceSummary, PriceDepth, TradeRecord, LeaderboardEntry, 
    MarketStatus, TradingHoursResponse, ErrorResponse
)
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/price/summary",
    response_model=PriceSummary,
    responses={
        500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
    },
    summary="查詢股票價格摘要",
    description="查詢 SITC 股票的即時報價摘要，包括最後成交價、漲跌幅、最高最低價等資訊"
)
async def get_price_summary(
    public_service: PublicService = Depends(get_public_service)
) -> PriceSummary:
    """
    查詢 SITC 股票的即時報價摘要
    
    Returns:
        PriceSummary: 包含股票價格的完整摘要資訊
    """
    return await public_service.get_price_summary()


@router.get(
    "/price/depth",
    response_model=PriceDepth,
    responses={
        500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
    },
    summary="查詢五檔報價",
    description="查詢目前的五檔掛單（買一～五、賣一～五）"
)
async def get_price_depth(
    public_service: PublicService = Depends(get_public_service)
) -> PriceDepth:
    """
    查詢目前的五檔掛單
    
    Returns:
        PriceDepth: 買賣方各五檔的價格和數量
    """
    return await public_service.get_price_depth()


@router.get(
    "/price/trades",
    response_model=List[TradeRecord],
    responses={
        500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
    },
    summary="查詢最近成交記錄",
    description="查詢最近的股票成交記錄，可指定查詢數量"
)
async def get_recent_trades(
    limit: int = Query(20, ge=1, le=100, description="查詢筆數限制（1-100筆）"),
    public_service: PublicService = Depends(get_public_service)
) -> List[TradeRecord]:
    """
    查詢最近成交記錄
    
    Args:
        limit: 查詢筆數限制，預設 20 筆，最多 100 筆
        
    Returns:
        List[TradeRecord]: 成交記錄列表
    """
    return await public_service.get_recent_trades(limit)


@router.get(
    "/leaderboard",
    response_model=List[LeaderboardEntry],
    responses={
        500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
    },
    summary="查詢排行榜",
    description="查詢使用者排行榜，包含點數和股票價值"
)
async def get_leaderboard(
    public_service: PublicService = Depends(get_public_service)
) -> List[LeaderboardEntry]:
    """
    查詢排行榜
    
    Returns:
        List[LeaderboardEntry]: 按總資產排序的使用者排行榜
    """
    return await public_service.get_leaderboard()


@router.get(
    "/status",
    response_model=MarketStatus,
    responses={
        500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
    },
    summary="查詢市場狀態",
    description="查詢目前交易市場狀態，包括是否開放和開放時間"
)
async def get_market_status(
    public_service: PublicService = Depends(get_public_service)
) -> MarketStatus:
    """
    查詢目前交易市場狀態
    
    Returns:
        MarketStatus: 市場開放狀態和時間資訊
    """
    return await public_service.get_market_status()


@router.get(
    "/trading-hours",
    response_model=TradingHoursResponse,
    responses={
        500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
    },
    summary="查詢交易時間列表",
    description="查詢目前設定的交易時間段列表，包含目前是否在交易時間內"
)
async def get_trading_hours(
    public_service: PublicService = Depends(get_public_service)
) -> TradingHoursResponse:
    """
    查詢交易時間列表
    
    Returns:
        TradingHoursResponse: 交易時間段列表和目前狀態
    """
    return await public_service.get_trading_hours()


# 額外的便利端點

@router.get(
    "/price/current",
    summary="查詢目前股價",
    description="快速查詢目前股票價格"
)
async def get_current_price(
    public_service: PublicService = Depends(get_public_service)
):
    """查詢目前股價"""
    try:
        summary = await public_service.get_price_summary()
        return {
            "price": summary.last_price,
            "change": summary.change,
            "changePercent": summary.change_percent
        }
    except Exception as e:
        logger.error(f"Failed to get current price: {e}")
        return {
            "price": 20,
            "change": "+0",
            "changePercent": "+0.0%"
        }


@router.get(
    "/stats",
    summary="查詢系統統計",
    description="查詢系統基本統計資訊"
)
async def get_system_stats(
    public_service: PublicService = Depends(get_public_service)
):
    """查詢系統統計資訊"""
    try:
        from app.core.database import get_database, Collections
        db = get_database()
        
        # 統計基本資訊
        total_users = await db[Collections.USERS].count_documents({})
        total_trades = await db[Collections.STOCK_ORDERS].count_documents({"status": "filled"})
        pending_orders = await db[Collections.STOCK_ORDERS].count_documents({"status": "pending"})
        
        # 取得市場狀態
        market_status = await public_service.get_market_status()
        
        return {
            "totalUsers": total_users,
            "totalTrades": total_trades,
            "pendingOrders": pending_orders,
            "marketOpen": market_status.is_open,
            "timestamp": market_status.current_time
        }
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        return {
            "totalUsers": 0,
            "totalTrades": 0,
            "pendingOrders": 0,
            "marketOpen": False,
            "timestamp": "2025-05-29T00:00:00Z"
        }


@router.get(
    "/price/history",
    response_model=List[dict],
    responses={
        500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
    },
    summary="查詢歷史價格資料",
    description="查詢歷史股價資料，用於繪製走勢圖"
)
async def get_price_history(
    hours: int = Query(24, ge=1, le=168, description="查詢過去幾小時的資料（1-168小時）"),
    public_service: PublicService = Depends(get_public_service)
) -> List[dict]:
    """
    查詢歷史價格資料
    
    Args:
        hours: 查詢過去幾小時的資料，預設24小時，最多7天(168小時)
        
    Returns:
        List[dict]: 歷史價格資料列表，包含時間戳和價格
    """
    return await public_service.get_price_history(hours)
