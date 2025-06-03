from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ========== Public API Model ==========


# 股票價格摘要
class PriceSummary(BaseModel):
    last_price: float = Field(..., description="最後成交價", alias="lastPrice")
    change: str = Field(..., description="漲跌幅度")
    change_percent: str = Field(..., description="漲跌百分比", alias="changePercent")
    high: float = Field(..., description="最高價")
    low: float = Field(..., description="最低價")
    open: float = Field(..., description="開盤價")
    volume: int = Field(..., description="成交量")
    limit_percent: float = Field(..., description="漲跌限制百分比", alias="limitPercent")
    
    class Config:
        populate_by_name = True


# 委託簿條目
class OrderBookEntry(BaseModel):
    price: float = Field(..., description="價格")
    quantity: int = Field(..., description="數量")


# 五檔報價
class PriceDepth(BaseModel):
    buy: List[OrderBookEntry] = Field(..., description="買方掛單")
    sell: List[OrderBookEntry] = Field(..., description="賣方掛單")


# 成交記錄
class TradeRecord(BaseModel):
    price: float = Field(..., description="成交價格")
    quantity: int = Field(..., description="成交數量")
    timestamp: str = Field(..., description="成交時間")


# 排行榜條目
class LeaderboardEntry(BaseModel):
    username: str = Field(..., description="使用者名稱")
    team: str = Field(..., description="隊伍名稱")
    points: float = Field(..., description="點數")
    stock_value: float = Field(..., description="股票價值", alias="stockValue")
    
    class Config:
        populate_by_name = True


# 市場時間段
class MarketTimeSlot(BaseModel):
    start: int = Field(..., description="開始時間戳")
    end: int = Field(..., description="結束時間戳")


# 市場狀態
class MarketStatus(BaseModel):
    is_open: bool = Field(..., description="市場是否開放", alias="isOpen")
    current_time: str = Field(..., description="目前時間", alias="currentTime")
    open_time: List[MarketTimeSlot] = Field(..., description="開放時間列表", alias="openTime")
    
    class Config:
        populate_by_name = True


# ========== 管理員 API 相關模型 ==========

# 管理員登入請求
class AdminLoginRequest(BaseModel):
    password: str = Field(..., description="管理員密碼")


# 管理員登入回應
class AdminLoginResponse(BaseModel):
    token: str = Field(..., description="JWT Token")


# 使用者資產明細
class UserAssetDetail(BaseModel):
    username: str = Field(..., description="使用者名稱")
    team: str = Field(..., description="所屬隊伍")
    points: int = Field(..., description="點數餘額")
    stocks: int = Field(..., description="持股數量")
    avg_cost: float = Field(..., description="平均成本", alias="avgCost")
    stock_value: float = Field(..., description="股票價值", alias="stockValue")
    total: float = Field(..., description="總資產")
    
    class Config:
        populate_by_name = True


# 給點數請求
class GivePointsRequest(BaseModel):
    username: str = Field(..., description="目標使用者名稱")
    type: str = Field(..., description="操作類型：group 或 user")
    amount: int = Field(..., description="點數數量")


# 給點數回應
class GivePointsResponse(BaseModel):
    ok: bool = Field(True, description="操作結果")
    message: Optional[str] = Field(None, description="操作訊息")


# 公告請求
class AnnouncementRequest(BaseModel):
    title: str = Field(..., description="公告標題")
    message: str = Field(..., description="公告內容")
    broadcast: bool = Field(True, description="是否廣播到 Bot")


# 公告回應
class AnnouncementResponse(BaseModel):
    ok: bool = Field(True, description="操作結果")
    message: Optional[str] = Field(None, description="操作訊息")


# 市場時間更新請求
class MarketUpdateRequest(BaseModel):
    open_time: List[MarketTimeSlot] = Field(..., description="開放時間列表", alias="openTime")
    
    class Config:
        populate_by_name = True


# 市場時間更新回應
class MarketUpdateResponse(BaseModel):
    ok: bool = Field(True, description="操作結果")


# 漲跌限制設定請求
class MarketLimitRequest(BaseModel):
    limit_percent: float = Field(..., description="漲跌限制百分比", alias="limitPercent")
    
    class Config:
        populate_by_name = True


# 漲跌限制設定回應
class MarketLimitResponse(BaseModel):
    ok: bool = Field(True, description="操作結果")


# 錯誤回應
class ErrorResponse(BaseModel):
    detail: str = Field(..., description="錯誤詳情")
