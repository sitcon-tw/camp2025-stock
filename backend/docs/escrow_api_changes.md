# 圈存系統 API 響應變更說明

## 概述

實施圈存系統後，使用者現在有兩種餘額概念：
- **可用餘額** (`available_points` / `points`): 使用者可以立即使用的點數
- **圈存金額** (`escrow_amount`): 已被預訂但尚未消費的點數
- **總餘額** (`total_balance`): 可用餘額 + 圈存金額

## API 響應變更

### 1. 使用者投資組合 API (`/api/user/portfolio`)

**舊格式：**
```json
{
  "username": "user123",
  "points": 1000,
  "stocks": 50,
  "stockValue": 1000,
  "totalValue": 2000,
  "avgCost": 20.0
}
```

**新格式：**
```json
{
  "username": "user123",
  "points": 800,           // 可用餘額
  "escrowAmount": 200,     // 圈存金額
  "totalBalance": 1000,    // 總餘額
  "stocks": 50,
  "stockValue": 1000,
  "totalValue": 2000,      // 總資產 = 總餘額 + 股票價值
  "avgCost": 20.0
}
```

### 2. 管理員使用者資產查詢 API (`/api/admin/user-details`)

**舊格式：**
```json
{
  "username": "user123",
  "team": "Team A",
  "points": 1000,
  "stocks": 50,
  "avgCost": 20,
  "stockValue": 1000,
  "total": 2000
}
```

**新格式：**
```json
{
  "username": "user123",
  "team": "Team A",
  "points": 800,           // 可用餘額
  "escrowAmount": 200,     // 圈存金額
  "totalBalance": 1000,    // 總餘額
  "stocks": 50,
  "avgCost": 20,
  "stockValue": 1000,
  "total": 2000            // 總資產
}
```

### 3. 管理員使用者列表 API (`/api/admin/users`)

**新增字段：**
```json
{
  "id": "user123",
  "name": "User Name",
  "team": "Team A",
  "telegram_id": "123456789",
  "telegram_nickname": "UserNick",
  "enabled": true,
  "available_points": 800,     // 新增：可用餘額
  "escrow_amount": 200,        // 新增：圈存金額
  "total_balance": 1000,       // 新增：總餘額
  "points": 800,               // 向後相容
  "stock_amount": 50,
  "stock_value": 1000,         // 新增：股票價值
  "total_value": 2000,         // 總資產
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### 4. 新增使用者餘額詳情 API (`/api/user/balance/detail`)

**新 API 響應：**
```json
{
  "username": "user123",
  "availablePoints": 800,      // 可用餘額
  "escrowAmount": 200,         // 圈存金額
  "totalBalance": 1000         // 總餘額
}
```

### 5. 新增使用者圈存記錄 API (`/api/user/balance/escrows`)

**新 API 響應：**
```json
{
  "success": true,
  "data": {
    "escrows": [
      {
        "_id": "escrow123",
        "user_id": "user123",
        "amount": 200,
        "type": "stock_order",
        "status": "active",
        "created_at": "2024-01-01T00:00:00Z",
        "reference_id": "order456",
        "metadata": {
          "side": "buy",
          "quantity": 10,
          "price": 20
        }
      }
    ],
    "statistics": {
      "total_escrows": 1,
      "active_escrows": 1,
      "total_active_amount": 200
    }
  }
}
```

## 前端適配建議

### 1. 餘額顯示
```javascript
// 主要顯示可用餘額
const displayBalance = data.points; // 或 data.available_points

// 詳細信息顯示
const availablePoints = data.points;
const escrowAmount = data.escrowAmount || 0;
const totalBalance = data.totalBalance || (availablePoints + escrowAmount);
```

### 2. 餘額檢查
```javascript
// 檢查是否有足夠可用餘額進行交易
function canAffordTransaction(userBalance, amount) {
    return userBalance.points >= amount; // 只檢查可用餘額
}
```

### 3. 圈存狀態顯示
```javascript
// 顯示圈存信息
if (userBalance.escrowAmount > 0) {
    console.log(`有 ${userBalance.escrowAmount} 點正在圈存中`);
}
```

## 向後相容性

- `points` 字段保持不變，代表可用餘額
- 新增的字段都有預設值，不會破壞現有功能
- 總資產計算邏輯已更新，使用總餘額而非僅可用餘額

## 資料庫變更

### Users Collection 新增字段：
```javascript
{
  // 現有字段...
  "points": 800,           // 可用餘額
  "escrow_amount": 200,    // 圈存金額 (新增)
  // 其他字段...
}
```

### 新增 Collections：
- `escrows`: 圈存記錄
- `escrow_logs`: 圈存操作日誌

## 管理員功能

### 1. 圈存管理 API (`/api/admin/escrow/*`)
- 查看使用者圈存記錄
- 取消異常圈存
- 系統健康檢查
- 圈存統計信息

### 2. 使用者餘額初始化
```bash
# 為現有使用者初始化圈存字段
python scripts/init_user_escrow_fields.py
```

### 3. 圈存系統測試
```bash
# 運行圈存系統完整測試
python scripts/test_escrow_system.py
```

這些變更確保了系統的資金安全性，同時保持了 API 的向後相容性。