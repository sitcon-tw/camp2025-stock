# 服務目錄結構

## 📁 完整的服務組織架構

```
app/services/
├── __init__.py                           # 統一導入入口，向後相容性
├── user_service_backup.py                # 原始檔案備份
│
├── 📁 user_management/                   # 用戶管理模組
│   ├── __init__.py
│   ├── base_service.py                   # 基礎服務類別
│   ├── user_service.py                   # 用戶管理服務
│   └── transfer_service.py               # 點數轉帳服務
│
├── 📁 trading/                           # 交易模組
│   ├── __init__.py
│   └── trading_service.py                # 股票交易服務
│
├── 📁 market/                            # 市場模組
│   ├── __init__.py
│   ├── market_service.py                 # 市場管理服務
│   └── ipo_service.py                    # IPO 服務
│
├── 📁 matching/                          # 撮合模組
│   ├── __init__.py
│   ├── order_matching_service.py         # 訂單撮合服務
│   └── matching_scheduler.py             # 撮合調度器
│
├── 📁 admin/                             # 管理模組
│   ├── __init__.py
│   └── admin_service.py                  # 管理員服務
│
├── 📁 core/                              # 核心模組
│   ├── __init__.py
│   ├── cache_service.py                  # 快取服務
│   ├── cache_invalidation.py             # 快取失效處理
│   ├── public_service.py                 # 公開 API 服務
│   └── rbac_service.py                   # 權限控制服務
│
├── 📁 system/                            # 系統管理模組
│   ├── __init__.py
│   ├── student_service.py                # 學生管理服務
│   └── debt_service.py                   # 債務管理服務
│
├── 📁 notification/                      # 通知模組
│   ├── __init__.py
│   └── notification_service.py           # 通知服務
│
├── 📁 game/                              # 遊戲模組
│   ├── __init__.py
│   └── game_service.py                   # 遊戲邏輯服務
│
└── 📁 infrastructure/                    # 基礎設施模組
    ├── __init__.py
    ├── distributed_system_integrator.py  # 分散式系統整合器
    ├── event_bus_service.py              # 事件總線服務
    ├── sharded_order_processor.py        # 分片訂單處理器
    ├── sharding_service.py               # 分片服務
    └── order_queue_service.py            # 訂單佇列服務
```

## 📋 服務清單與依賴注入函數

### 用戶管理模組 (user_management/)
| 服務 | 類別 | 依賴注入函數 | 職責 |
|------|------|-------------|------|
| BaseService | `BaseService` | `get_base_service()` | 所有服務的基礎類別 |
| UserService | `UserService` | `get_user_service()` | 用戶管理核心功能 |
| TransferService | `TransferService` | `get_transfer_service()` | 點數轉帳功能 |

### 交易模組 (trading/)
| 服務 | 類別 | 依賴注入函數 | 職責 |
|------|------|-------------|------|
| TradingService | `TradingService` | `get_trading_service()` | 股票交易執行 |

### 市場模組 (market/)
| 服務 | 類別 | 依賴注入函數 | 職責 |
|------|------|-------------|------|
| MarketService | `MarketService` | `get_market_service()` | 市場狀態管理 |
| IPOService | `IPOService` | `get_ipo_service()` | IPO 初次公開發行 |

### 撮合模組 (matching/)
| 服務 | 類別 | 依賴注入函數 | 職責 |
|------|------|-------------|------|
| OrderMatchingService | `OrderMatchingService` | `get_order_matching_service()` | 訂單撮合引擎 |
| MatchingScheduler | `MatchingScheduler` | `get_matching_scheduler()` | 撮合調度器 |

### 管理模組 (admin/)
| 服務 | 類別 | 依賴注入函數 | 職責 |
|------|------|-------------|------|
| AdminService | `AdminService` | `get_admin_service()` | 管理員功能 |

### 核心模組 (core/)
| 服務 | 類別 | 依賴注入函數 | 職責 |
|------|------|-------------|------|
| CacheService | `CacheService` | `get_cache_service()` | 快取管理 |
| PublicService | `PublicService` | `get_public_service()` | 公開 API |
| RBACService | `RBACManagementService` | `get_rbac_service()` | 權限控制 |

### 系統管理模組 (system/)
| 服務 | 類別 | 依賴注入函數 | 職責 |
|------|------|-------------|------|
| StudentService | `StudentService` | `get_student_service()` | 學生管理 |
| DebtService | `DebtService` | `get_debt_service()` | 債務管理 |

### 通知模組 (notification/)
| 服務 | 類別 | 依賴注入函數 | 職責 |
|------|------|-------------|------|
| NotificationService | `NotificationService` | `get_notification_service()` | 通知服務 |

### 遊戲模組 (game/)
| 服務 | 類別 | 依賴注入函數 | 職責 |
|------|------|-------------|------|
| GameService | `GameService` | `get_game_service()` | 遊戲邏輯 |

### 基礎設施模組 (infrastructure/)
| 服務 | 類別 | 依賴注入函數 | 職責 |
|------|------|-------------|------|
| DistributedSystemIntegrator | `DistributedSystemIntegrator` | `get_distributed_system_integrator()` | 分散式系統整合 |
| EventBusService | `EventBusService` | `get_event_bus_service()` | 事件總線 |
| ShardedOrderProcessor | `ShardedOrderProcessor` | `get_sharded_order_processor()` | 分片訂單處理 |
| ShardingService | `UserShardingService` | `get_sharding_service()` | 分片服務 |
| OrderQueueService | `OrderQueueService` | `get_order_queue_service()` | 訂單佇列 |

## 🔄 服務依賴關係圖

```
UserService (用戶管理)
├── BaseService (基礎服務)
├── MarketService (市場服務)
├── TradingService (交易服務)
├── TransferService (轉帳服務)
└── OrderMatchingService (撮合服務)

TradingService (交易服務)
├── BaseService (基礎服務)
├── MarketService (市場服務)
└── OrderMatchingService (撮合服務)

OrderMatchingService (撮合服務)
├── BaseService (基礎服務)
├── MarketService (市場服務)
└── MatchingScheduler (撮合調度器)

MarketService (市場服務)
├── BaseService (基礎服務)
└── IPOService (IPO服務)

TransferService (轉帳服務)
└── BaseService (基礎服務)

AdminService (管理服務)
├── BaseService (基礎服務)
├── UserService (用戶服務)
└── NotificationService (通知服務)

PublicService (公開服務)
├── BaseService (基礎服務)
├── CacheService (快取服務)
└── MarketService (市場服務)

GameService (遊戲服務)
├── BaseService (基礎服務)
└── UserService (用戶服務)

Infrastructure Services (基礎設施服務)
├── DistributedSystemIntegrator (分散式系統整合器)
├── EventBusService (事件總線服務)
├── ShardedOrderProcessor (分片訂單處理器)
├── ShardingService (分片服務)
└── OrderQueueService (訂單佇列服務)
```

## 🎯 導入方式

### 推薦的模組化導入
```python
# 按模組導入（推薦）
from app.services.user_management import get_user_service
from app.services.trading import get_trading_service
from app.services.market import get_market_service
from app.services.matching import get_order_matching_service
from app.services.admin import get_admin_service
from app.infrastructure.container import get_public_service
from app.infrastructure.cache.cache_service import get_cache_service
from app.services.system import get_debt_service, get_student_service
from app.services.notification import get_notification_service
from app.services.game import get_game_service
from app.services.infrastructure import get_distributed_system_integrator
```

### 向後相容性導入
```python
# 統一導入（向後相容）
from app.services import (
    get_user_service, get_trading_service, get_market_service,
    get_admin_service, get_public_service, get_cache_service,
    get_debt_service, get_student_service, get_notification_service,
    get_game_service, get_order_matching_service
)
```

## 📊 重構統計

- **原始檔案**: 1 個巨大的 user_service.py (3508 行)
- **重構後**: 9 個模組，18 個服務檔案
- **程式碼組織**: 按功能域清晰分組
- **依賴注入**: 統一的依賴注入模式
- **向後相容**: 100% 向後相容性
- **可維護性**: 大幅提升
- **可測試性**: 每個服務可獨立測試

這個組織結構遵循了：
- 📝 **單一職責原則** (SRP)
- 🔄 **依賴注入原則** (DIP)
- 🏗️ **模組化設計**
- 🎯 **領域驅動設計** (DDD)
- 📦 **清晰的邊界分離**