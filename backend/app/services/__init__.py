"""
服務層模組

重構後的服務架構：
- user_management/: 使用者管理相關服務
- trading/: 交易相關服務  
- market/: 市場管理服務
- matching/: 撮合引擎服務
- admin/: 管理服務
- core/: 核心服務 (快取、公開API、權限)
- infrastructure/: 基礎設施服務
- game/: 遊戲相關服務
- notification/: 通知服務
- system/: 系統管理服務

向後相容性導入，保持現有 API 不變
"""

# 向後相容性導入 - 核心服務
from .user_management import UserService, get_user_service
from .user_management import TransferService, get_transfer_service
from .trading import TradingService, get_trading_service
from .market import MarketService, get_market_service
from .matching import OrderMatchingService, get_order_matching_service

# 向後相容性導入 - 其他服務
from .admin import AdminService, get_admin_service
from .core import PublicService, get_public_service
from .core import CacheService, get_cache_service
from .core import get_cache_invalidator
from .core import RBACManagementService, get_rbac_management_service
from .system import DebtService, get_debt_service
from .system import StudentService, get_student_service
from .notification import NotificationService, get_notification_service
from .game import GameService, get_game_service
from .matching import MatchingScheduler, get_matching_scheduler
from .market import IPOService, get_ipo_service

__all__ = [
    # 使用者管理
    "UserService",
    "get_user_service",
    "TransferService", 
    "get_transfer_service",
    # 交易
    "TradingService",
    "get_trading_service",
    # 市場
    "MarketService",
    "get_market_service",
    "IPOService",
    "get_ipo_service",
    # 撮合
    "OrderMatchingService",
    "get_order_matching_service",
    "MatchingScheduler",
    "get_matching_scheduler",
    # 管理
    "AdminService",
    "get_admin_service",
    # 核心
    "PublicService",
    "get_public_service",
    "CacheService",
    "get_cache_service",
    "get_cache_invalidator",
    "RBACManagementService",
    "get_rbac_management_service",
    # 系統
    "DebtService",
    "get_debt_service",
    "StudentService",
    "get_student_service",
    # 通知
    "NotificationService",
    "get_notification_service",
    # 遊戲
    "GameService",
    "get_game_service",
]