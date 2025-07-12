# Point Logs 資料結構問題分析報告

## 問題描述

前端 Point History 頁面無法查詢到使用者的點數變動記錄，原因是 `point_logs` 集合中的 `user_id` 欄位與前端查詢使用的使用者 ID 格式不匹配。

## 根本原因分析

### 資料結構不匹配

1. **users 集合結構**:
   ```javascript
   {
     "_id": ObjectId("..."),        // MongoDB 自動生成的 ObjectId
     "id": "9052521455",            // 使用者永久 ID（字符串）
     "name": "使用者姓名",
     "telegram_id": 6978842385,
     // ... 其他欄位
   }
   ```

2. **point_logs 集合結構**:
   ```javascript
   {
     "_id": ObjectId("..."),
     "user_id": ObjectId("..."),    // 儲存的是 users._id，不是 users.id！
     "type": "admin_grant",
     "amount": 100,
     "created_at": ISODate("..."),
     "balance_after": 200
   }
   ```

### 程式碼問題位置

**backend/app/services/admin_service.py 第 466-485 行**：

```python
async def _log_point_change(self, user_id: str, operation_type: str,
                            amount: int, note: str = ""):
    try:
        # 取得使用者目前餘額
        user = await self.db[Collections.USERS].find_one({"_id": user_id})
        current_balance = user.get("points", 0) if user else 0

        log_entry = {
            "user_id": user_id,  # ❌ 問題：這裡儲存的是 MongoDB _id
            "type": operation_type,
            "amount": amount,
            "note": note,
            "created_at": datetime.now(timezone.utc),
            "balance_after": current_balance
        }

        await self.db[Collections.POINT_LOGS].insert_one(log_entry)
```

**調用位置（第 177、200、232 行等）**：
```python
await self._log_point_change(
    user["_id"],  # ❌ 問題：傳入 MongoDB _id 而不是 user.id
    "admin_grant",
    request.amount,
    f"管理員給予點數: {request.amount} 點"
)
```

### 前端查詢邏輯

前端使用 JWT token 中的 `user_id`（例如 "9052521455"）來查詢：

```javascript
// 前端查詢邏輯
const userId = user.id; // "9052521455" 
// 查詢 point_logs 時使用這個 ID，但 point_logs.user_id 儲存的是 ObjectId
```

## 解決方案

### 方案一：修改後端 point_logs 儲存邏輯（推薦）

修改 `admin_service.py` 中的 `_log_point_change` 方法：

```python
async def _log_point_change(self, user_mongo_id: str, operation_type: str,
                            amount: int, note: str = ""):
    try:
        # 取得使用者資料
        user = await self.db[Collections.USERS].find_one({"_id": user_mongo_id})
        if not user:
            logger.error(f"User not found for _id: {user_mongo_id}")
            return
            
        current_balance = user.get("points", 0)

        log_entry = {
            "user_id": user["id"],  # ✅ 修正：使用 user.id 而不是 _id
            "type": operation_type,
            "amount": amount,
            "note": note,
            "created_at": datetime.now(timezone.utc),
            "balance_after": current_balance
        }

        await self.db[Collections.POINT_LOGS].insert_one(log_entry)
```

### 方案二：修改前端查詢邏輯

如果不能修改後端，前端需要兩步查詢：

```javascript
// 1. 先查詢 users 集合獲取 MongoDB _id
const userDoc = await fetch(`/api/user/profile`);
const mongoId = userDoc._id;

// 2. 使用 MongoDB _id 查詢 point_logs
const pointLogs = await fetch(`/api/user/point-logs?user_id=${mongoId}`);
```

## 建議實施方案

**推薦使用方案一**，原因：

1. **資料一致性**：`user.id` 是系統設計的永久標識符，應該在所有相關表中使用
2. **查詢效率**：避免前端需要額外的查詢步驟
3. **維護性**：保持資料模型的邏輯一致性
4. **API 設計**：符合 RESTful API 設計原則

## 影響範圍

需要檢查以下檔案中是否有類似問題：

1. `app/services/user_service.py` - 使用者相關的點數記錄
2. `app/services/transfer_service.py` - 轉帳相關的點數記錄  
3. `app/routers/user_refactored.py` - QR Code 兌換功能
4. 其他可能創建 point_logs 記錄的服務

## 測試驗證

修復後需要驗證：

1. 新創建的 point_logs 記錄使用正確的 user_id 格式
2. 前端 Point History 頁面能正確顯示歷史記錄
3. 既有的錯誤格式記錄需要資料遷移（可選）

## 資料遷移（可選）

如果需要修復既有的錯誤記錄：

```javascript
// MongoDB 腳本，將既有的 ObjectId 格式 user_id 轉換為字符串格式
db.point_logs.find({}).forEach(function(log) {
    if (typeof log.user_id === "object") {
        const user = db.users.findOne({"_id": log.user_id});
        if (user && user.id) {
            db.point_logs.updateOne(
                {"_id": log._id},
                {"$set": {"user_id": user.id}}
            );
        }
    }
});
```