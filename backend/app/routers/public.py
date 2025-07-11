from fastapi import APIRouter, Depends, Query
from app.services.public_service import PublicService, get_public_service
from app.schemas.public import (
    PriceSummary, PriceDepth, TradeRecord, LeaderboardEntry, 
    MarketStatus, TradingHoursResponse, ErrorResponse, PublicAnnouncement,
    MarketPriceInfo
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


@router.get(
    "/announcements",
    response_model=List[PublicAnnouncement],
    responses={
        500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
    },
    summary="查詢公告列表",
    description="查詢所有公開公告，按時間倒序排列"
)
async def get_announcements(
    limit: int = Query(10, ge=1, le=50, description="查詢筆數限制（1-50筆）"),
    public_service: PublicService = Depends(get_public_service)
) -> List[PublicAnnouncement]:
    """
    查詢公告列表
    
    Args:
        limit: 查詢筆數限制，預設10筆，最多50筆
        
    Returns:
        List[PublicAnnouncement]: 公告列表，按時間倒序排列
    """
    return await public_service.get_public_announcements(limit)


@router.get(
    "/ipo/status",
    responses={
        500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
    },
    summary="查詢IPO狀態",
    description="查詢目前IPO（首次公開發行）的狀態，包括剩餘股數和價格"
)
async def get_ipo_status(
    public_service: PublicService = Depends(get_public_service)
):
    """
    查詢IPO狀態
    
    Returns:
        dict: IPO狀態資訊，包含初始股數、剩餘股數、初始價格等
    """
    return await public_service.get_ipo_status()


@router.get(
    "/trading/stats",
    responses={
        500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
    },
    summary="查詢交易統計",
    description="查詢今日交易統計資訊，包括成交筆數、成交額、成交股數"
)
async def get_trading_stats(
    public_service: PublicService = Depends(get_public_service)
):
    """
    查詢今日交易統計
    
    Returns:
        dict: 交易統計資訊，包含成交筆數、成交額、成交股數
    """
    return await public_service.get_daily_trading_stats()


@router.get(
    "/market/price-info",
    response_model=MarketPriceInfo,
    responses={
        500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
    },
    summary="查詢市場價格資訊",
    description="查詢目前股價、收盤價、下次開盤初始價等市場價格資訊"
)
async def get_market_price_info(
    public_service: PublicService = Depends(get_public_service)
) -> MarketPriceInfo:
    """
    查詢市場價格資訊
    
    Returns:
        MarketPriceInfo: 市場價格資訊，包含：
        - currentPrice: 目前股價
        - closingPrice: 上次收盤價
        - openingPrice: 下次開盤初始價 (等於上次收盤價)
        - lastCloseTime: 上次收盤時間
        - marketIsOpen: 市場是否開盤
        - lastTradeTime: 最後成交時間
    """
    return await public_service.get_market_price_info()


@router.get(
    "/transfer/fee-config",
    responses={
        500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
    },
    summary="查詢轉帳手續費設定",
    description="查詢目前轉帳手續費率和最低手續費設定"
)
async def get_transfer_fee_config():
    """
    查詢轉帳手續費設定
    
    Returns:
        dict: 轉帳手續費設定，包含：
        - feeRate: 手續費率 (%)
        - minFee: 最低手續費 (點數)
    """
    try:
        from app.core.database import get_database, Collections
        
        db = get_database()
        
        # 查詢手續費設定
        fee_config = await db[Collections.MARKET_CONFIG].find_one({
            "type": "transfer_fee"
        })
        
        if fee_config:
            return {
                "feeRate": fee_config.get("fee_rate", 10.0),
                "minFee": fee_config.get("min_fee", 1)
            }
        else:
            # 如果沒有設定，回傳預設值
            return {
                "feeRate": 10.0,
                "minFee": 1
            }
        
    except Exception as e:
        logger.error(f"Failed to get transfer fee config: {e}")
        return {
            "feeRate": 10.0,
            "minFee": 1
        }


# @router.post(
#     "/community/verify",
#     responses={
#         400: {"model": ErrorResponse, "description": "請求參數錯誤"},
#         401: {"model": ErrorResponse, "description": "密碼錯誤"},
#         500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
#     },
#     summary="社群密碼驗證",
#     description="驗證密碼並自動檢測對應的社群"
# )
# async def verify_community_password(
#     password: str = Query(..., description="社群密碼")
# ):
#     """
#     社群密碼驗證（自動檢測社群）
    
#     Args:
#         password: 社群密碼
        
#     Returns:
#         dict: 驗證結果，包含：
#         - success: 是否驗證成功
#         - community: 社群名稱（驗證成功時）
#         - message: 錯誤訊息（驗證失敗時）
#     """
#     try:
#         # 社群密碼配置
#         COMMUNITY_PASSWORDS = {
#             "SITCON 學生計算機年會": "Tiger9@Vault!Mo0n#42*",
#             "OCF 開放文化基金會": "Ocean^CultuR3$Rise!888",
#             "Ubuntu 台灣社群": "Ubun2u!Taipei@2025^Rocks",
#             "MozTW 社群": "MozTw$Fox_@42Jade*Fire",
#             "COSCUP 開源人年會": "COde*0p3n#Sun5et!UP22",
#             "Taiwan Security Club": "S3curE@Tree!^Night_CLUB99",
#             "SCoML 學生機器學習社群": "M@chin3Zebra_Learn#504*",
#             "綠洲計畫 LZGH": "0@si5^L!ght$Grow*Green88",
#             "PyCon TW": "PyTh0n#Conf!Luv2TW@2025"
#         }
        
#         # 尋找密碼對應的社群
#         for community_name, community_password in COMMUNITY_PASSWORDS.items():
#             if community_password == password:
#                 return {
#                     "success": True,
#                     "community": community_name,
#                     "message": "驗證成功"
#                 }
        
#         # 密碼不對應任何社群
#         return {
#             "success": False,
#             "message": "密碼錯誤或不存在對應的社群"
#         }
        
#     except Exception as e:
#         logger.error(f"Community password verification failed: {e}")
#         return {
#             "success": False,
#             "message": "驗證過程發生錯誤"
#         }


# @router.post(
#     "/community/give-points",
#     responses={
#         400: {"model": ErrorResponse, "description": "請求參數錯誤"},
#         401: {"model": ErrorResponse, "description": "社群密碼錯誤"},
#         404: {"model": ErrorResponse, "description": "找不到學員"},
#         500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
#     },
#     summary="社群攤位發放點數",
#     description="社群攤位給學員發放點數"
# )
# async def community_give_points(
#     community_password: str = Query(..., description="社群密碼"),
#     student_username: str = Query(..., description="學員用戶名"),
#     points: int = Query(..., description="發放點數", ge=1, le=1000),
#     note: str = Query("社群攤位獎勵", description="備註"),
#     create_if_not_exists: bool = Query(False, description="如果學員不存在是否創建")
# ):
#     """
#     社群攤位發放點數
    
#     Args:
#         community_password: 社群密碼
#         student_username: 學員用戶名
#         points: 發放點數
#         note: 備註
        
#     Returns:
#         dict: 發放結果
#     """
#     try:
#         from app.core.database import get_database, Collections
        
#         # 社群密碼配置
#         COMMUNITY_PASSWORDS = {
#             "SITCON 學生計算機年會": "Tiger9@Vault!Mo0n#42*",
#             "OCF 開放文化基金會": "Ocean^CultuR3$Rise!888",
#             "Ubuntu 台灣社群": "Ubun2u!Taipei@2025^Rocks",
#             "MozTW 社群": "MozTw$Fox_@42Jade*Fire",
#             "COSCUP 開源人年會": "COde*0p3n#Sun5et!UP22",
#             "Taiwan Security Club": "S3curE@Tree!^Night_CLUB99",
#             "SCoML 學生機器學習社群": "M@chin3Zebra_Learn#504*",
#             "綠洲計畫 LZGH": "0@si5^L!ght$Grow*Green88",
#             "PyCon TW": "PyTh0n#Conf!Luv2TW@2025"
#         }
        
#         # 驗證社群密碼
#         community_name = None
#         for name, password in COMMUNITY_PASSWORDS.items():
#             if password == community_password:
#                 community_name = name
#                 break
        
#         if not community_name:
#             return {
#                 "success": False,
#                 "message": "社群密碼錯誤"
#             }
        
#         db = get_database()
        
#         # 查找學員 (可能是telegram_id或username)
#         user = None
        
#         # 首先嘗試作為telegram_id查找
#         try:
#             telegram_id = int(student_username)
#             logger.info(f"嘗試用telegram_id查找: {telegram_id}")
#             user = await db[Collections.USERS].find_one({
#                 "telegram_id": telegram_id
#             })
#             if user:
#                 logger.info(f"通過telegram_id找到用戶: {user.get('username', 'unknown')}")
#         except ValueError:
#             logger.info(f"無法轉換為數字，嘗試用username查找: {student_username}")
        
#         # 如果沒找到，嘗試作為字符串格式的telegram_id
#         if not user:
#             logger.info(f"嘗試用字符串格式的telegram_id查找: {student_username}")
#             user = await db[Collections.USERS].find_one({
#                 "telegram_id": student_username
#             })
#             if user:
#                 logger.info(f"通過字符串telegram_id找到用戶: {user.get('username', 'unknown')}")
        
#         # 最後嘗試作為username查找
#         if not user:
#             logger.info(f"嘗試用username查找: {student_username}")
#             user = await db[Collections.USERS].find_one({
#                 "username": student_username
#             })
#             if user:
#                 logger.info(f"通過username找到用戶: {user.get('username', 'unknown')}")
        
#         if not user:
#             if create_if_not_exists:
#                 # 創建新學員
#                 try:
#                     telegram_id = int(student_username)
#                     user = {
#                         "telegram_id": telegram_id,
#                         "username": f"user_{telegram_id}",
#                         "points": 0,
#                         "stocks": 0,
#                         "created_at": datetime.now(timezone.utc),
#                         "updated_at": datetime.now(timezone.utc)
#                     }
#                     result = await db[Collections.USERS].insert_one(user)
#                     user["_id"] = result.inserted_id
#                     logger.info(f"創建新學員: {user['username']} (ID: {telegram_id})")
#                 except ValueError:
#                     return {
#                         "success": False,
#                         "message": f"無法創建學員，學員ID必須是數字: {student_username}"
#                     }
#             else:
#                 # 提供更詳細的調試資訊
#                 logger.error(f"找不到學員 {student_username}, 嘗試查詢附近的用戶...")
                
#                 # 查詢一些示例用戶以供調試，顯示所有字段
#                 try:
#                     sample_users = await db[Collections.USERS].find({}).limit(3).to_list(length=3)
                    
#                     sample_info = []
#                     for u in sample_users:
#                         user_info = {
#                             "_id": str(u.get("_id", "unknown")),
#                             "username": u.get("username", "unknown"),
#                             "telegram_id": u.get("telegram_id", "unknown"),
#                             "id": u.get("id", "unknown")  # 可能有其他ID字段
#                         }
#                         sample_info.append(str(user_info))
                    
#                     return {
#                         "success": False,
#                         "message": f"找不到學員: {student_username}",
#                         "debug_info": f"用戶結構範例: {sample_info}",
#                         "tip": "可以加上參數 create_if_not_exists=true 來自動創建學員"
#                     }
#                 except Exception as e:
#                     return {
#                         "success": False,
#                         "message": f"找不到學員: {student_username}"
#                     }
        
#         # 發放點數
#         from datetime import datetime, timezone
#         now = datetime.now(timezone.utc)
        
#         # 更新學員點數
#         result = await db[Collections.USERS].update_one(
#             {"_id": user["_id"]},
#             {
#                 "$inc": {"points": points},
#                 "$set": {"updated_at": now}
#             }
#         )
        
#         if result.modified_count == 0:
#             return {
#                 "success": False,
#                 "message": "更新學員點數失敗"
#             }
        
#         # 記錄點數歷史
#         point_record = {
#             "user_id": user["_id"],  # 使用 ObjectId 以保持與查詢邏輯一致
#             "username": student_username,
#             "amount": points,
#             "balance_after": user["points"] + points,
#             "type": "community_reward",
#             "note": f"{note} (來自 {community_name})",
#             "source": "community_booth",
#             "community": community_name,
#             "created_at": now
#         }
        
#         await db[Collections.POINT_LOGS].insert_one(point_record)
        
#         logger.info(f"社群 {community_name} 給學員 {student_username} 發放了 {points} 點數")
        
#         return {
#             "success": True,
#             "message": f"成功給 {student_username} 發放 {points} 點數",
#             "student": student_username,
#             "points": points,
#             "new_balance": user["points"] + points,
#             "community": community_name
#         }
        
#     except Exception as e:
#         logger.error(f"社群發放點數失敗: {e}")
#         return {
#             "success": False,
#             "message": "發放點數時發生錯誤"
#         }
