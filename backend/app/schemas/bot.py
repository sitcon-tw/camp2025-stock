from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any, Dict
from app.schemas.user import (
    UserRegistrationResponse, UserPortfolio, StockOrderResponse,
    TransferResponse, UserPointLog, UserStockOrder
)


# ========== BOT 專用請求模型 ==========


class BotStockOrderRequest(BaseModel):
    """BOT 股票訂單請求 - 包含 from_user"""
    from_user: str = Field(..., description="使用者id")
    order_type: str = Field(..., description="訂單類型：market 或 limit")
    side: str = Field(..., description="買賣方向：buy 或 sell")
    quantity: int = Field(..., gt=0, description="數量")
    price: Optional[int] = Field(None, gt=0, description="價格（元，限價單必填）")
    
    @validator('order_type')
    def validate_order_type(cls, v):
        if v not in ['market', 'limit']:
            raise ValueError('order_type must be "market" or "limit"')
        return v
    
    @validator('side')
    def validate_side(cls, v):
        if v not in ['buy', 'sell']:
            raise ValueError('side must be "buy" or "sell"')
        return v
    
    @validator('price')
    def validate_price_for_limit_order(cls, v, values):
        if values.get('order_type') == 'limit' and v is None:
            raise ValueError('Price is required for limit orders')
        return v


class BotTransferRequest(BaseModel):
    """BOT 轉帳請求 - 包含 from_user"""
    from_user: str = Field(..., description="轉帳發起人使用者名")
    to_username: str = Field(..., description="收款人使用者名")
    amount: int = Field(..., gt=0, description="轉帳金額")
    note: Optional[str] = Field(None, max_length=200, description="備註")


# ========== BOT 查詢請求模型 ==========

class BotPortfolioRequest(BaseModel):
    """BOT 查詢投資組合請求"""
    from_user: str = Field(..., description="使用者id")


class BotPointHistoryRequest(BaseModel):
    """BOT 查詢點數記錄請求"""
    from_user: str = Field(..., description="使用者id")
    limit: int = Field(default=50, gt=0, le=100, description="查詢筆數限制")


class BotStockOrdersRequest(BaseModel):
    """BOT 查詢股票訂單請求"""
    from_user: str = Field(..., description="使用者id")
    limit: int = Field(default=50, gt=0, le=100, description="查詢筆數限制")


class BotProfileRequest(BaseModel):
    """BOT 查詢使用者資料請求"""
    from_user: str = Field(..., description="使用者id")




# ========== Telegram Webhook 和 Broadcast 模型 ==========

class TelegramWebhookRequest(BaseModel):
    """Telegram Webhook 請求模型"""
    update_id: int = Field(..., description="更新 ID")
    message: Optional[Dict[str, Any]] = Field(None, description="訊息內容")
    callback_query: Optional[Dict[str, Any]] = Field(None, description="回調查詢")
    # 可以根據需要添加更多 Telegram API 欄位


class BroadcastRequest(BaseModel):
    """廣播訊息請求模型"""
    title: str = Field(..., description="訊息標題")
    message: str = Field(..., description="訊息內容")
    groups: List[int] = Field(..., description="目標群組 ID 列表")


class BroadcastAllRequest(BaseModel):
    """全員廣播訊息請求模型"""
    title: str = Field(..., description="訊息標題")
    message: str = Field(..., description="訊息內容")


class BroadcastResponse(BaseModel):
    """廣播回應模型"""
    ok: bool = Field(True, description="操作結果")
    message: Optional[str] = Field(None, description="回應訊息")
