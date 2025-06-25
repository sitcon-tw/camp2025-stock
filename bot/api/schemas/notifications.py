from typing import List, Optional, Dict, Any

from pydantic import BaseModel


class DMRequest(BaseModel):
    user_id: int
    message: str
    parse_mode: Optional[str] = "MarkdownV2"


class BulkDMRequest(BaseModel):
    user_ids: List[int]
    message: str
    parse_mode: Optional[str] = "MarkdownV2"
    delay_seconds: Optional[float] = 0.1


class NotificationRequest(BaseModel):
    user_id: int
    notification_type: str
    title: str
    content: str
    additional_data: Optional[Dict[str, Any]] = None


class TradeNotificationRequest(BaseModel):
    user_id: int
    action: str  # "buy" or "sell"
    quantity: int
    price: float
    total_amount: float
    order_id: Optional[str] = None


class TransferNotificationRequest(BaseModel):
    user_id: int
    transfer_type: str  # "sent" or "received"
    amount: float
    other_user: str
    transfer_id: Optional[str] = None


class SystemNotificationRequest(BaseModel):
    user_id: int
    title: str
    content: str
    priority: Optional[str] = "normal"