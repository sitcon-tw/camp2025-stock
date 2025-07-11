# MongoDB WriteConflict 錯誤解決方案

## 問題描述

當多個使用者同時使用系統時，會出現 MongoDB WriteConflict 錯誤：

```
WriteConflict during plan execution and yielding is disabled. 
Please retry your operation or multi-document transaction.
```

這是因為 MongoDB 在高併發環境中，多個事務同時修改相同文檔時產生的衝突。

## 解決方案

### 1. 增強重試機制

**改進項目：**
- 將重試次數從 5 次增加到 8 次
- 重試延遲從 5ms 減少到 3ms
- 添加隨機 jitter (0.8-1.2倍) 避免雷群效應
- 指數退避係數從 1.5 增加到 1.6

**涉及功能：**
- 市價單執行 (`_execute_market_order`)
- 訂單撮合 (`_match_orders`)
- 點數轉帳 (`transfer_points`)
- 限價單掛單 (`_insert_order_with_retry`)

### 2. 統一的錯誤監控

**新增功能：**
- 寫入衝突統計記錄
- 每 60 秒輸出統計報告
- 按操作類型分類統計

**監控類型：**
- `market_order`: 市價單執行衝突
- `order_matching`: 訂單撮合衝突
- `order_insert`: 訂單插入衝突
- `point_transfer`: 點數轉帳衝突

### 3. 代碼改進詳情

#### 3.1 市價單執行改進

```python
async def _execute_market_order(self, user_oid: ObjectId, order_doc: dict) -> StockOrderResponse:
    """執行市價單交易，帶增強重試機制"""
    max_retries = 8  # 增加重試次數至 8 次
    retry_delay = 0.003  # 3ms 初始延遲
    
    for attempt in range(max_retries):
        try:
            # ... 執行邏輯 ...
        except Exception as e:
            if "WriteConflict" in str(e):
                if attempt < max_retries - 1:
                    self._log_write_conflict("market_order", attempt, max_retries)
                    jitter = random.uniform(0.8, 1.2)
                    await asyncio.sleep(retry_delay * jitter)
                    retry_delay *= 1.6
                    continue
```

#### 3.2 訂單撮合改進

```python
async def _match_orders(self, buy_order: dict, sell_order: dict):
    """撮合訂單，帶增強重試機制"""
    max_retries = 8
    retry_delay = 0.003
    
    for attempt in range(max_retries):
        try:
            # ... 撮合邏輯 ...
        except Exception as e:
            if "WriteConflict" in str(e):
                if attempt < max_retries - 1:
                    self._log_write_conflict("order_matching", attempt, max_retries)
                    # 隨機延遲重試
```

#### 3.3 轉帳服務改進

```python
async def transfer_points(self, from_user_id: str, request: TransferRequest) -> TransferResponse:
    """轉帳點數，帶增強重試機制"""
    max_retries = 8
    retry_delay = 0.003
    
    for attempt in range(max_retries):
        try:
            # ... 轉帳邏輯 ...
        except Exception as e:
            if "WriteConflict" in str(e):
                # 重試邏輯
```

#### 3.4 新增限價單插入重試

```python
async def _insert_order_with_retry(self, order_doc: dict):
    """帶重試機制的訂單插入"""
    max_retries = 5
    retry_delay = 0.003
    
    for attempt in range(max_retries):
        try:
            return await self.db[Collections.STOCK_ORDERS].insert_one(order_doc)
        except Exception as e:
            if "WriteConflict" in str(e):
                # 重試邏輯
```

### 4. 監控統計功能

```python
class UserService:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        # ... 其他初始化 ...
        # 寫入衝突統計
        self.write_conflict_stats = defaultdict(int)
        self.last_conflict_log_time = time.time()
    
    def _log_write_conflict(self, operation: str, attempt: int, max_retries: int):
        """記錄寫入衝突統計"""
        self.write_conflict_stats[operation] += 1
        
        # 每 60 秒輸出一次統計報告
        current_time = time.time()
        if current_time - self.last_conflict_log_time > 60:
            total_conflicts = sum(self.write_conflict_stats.values())
            logger.warning(f"寫入衝突統計報告：總計 {total_conflicts} 次衝突")
            for op, count in self.write_conflict_stats.items():
                logger.warning(f"  {op}: {count} 次")
            self.last_conflict_log_time = current_time
```

### 5. 測試工具

提供了 `test_write_conflict.py` 高併發測試腳本：

**功能：**
- 併發交易測試
- 併發轉帳測試
- 混合負載測試

**使用方法：**
```bash
cd backend
python test_write_conflict.py
```

### 6. 性能改進預期

**改進前：**
- 重試 5 次，固定延遲
- 容易出現雷群效應
- 缺乏統計監控

**改進後：**
- 重試 8 次，隨機延遲
- 避免雷群效應
- 完整統計監控
- 更快的初始重試速度

**預期效果：**
- 減少 WriteConflict 錯誤發生率
- 提高系統併發處理能力
- 更好的錯誤監控和診斷
- 提升使用者體驗

### 7. 注意事項

1. **MongoDB 配置**：確保 MongoDB 運行在 replica set 模式以支援事務
2. **監控日誌**：留意 WriteConflict 統計報告，了解系統負載情況
3. **性能調優**：根據實際負載調整重試參數
4. **資源消耗**：重試機制會增加系統負載，需平衡性能和可靠性

### 8. 未來優化方向

1. **分片優化**：考慮使用 MongoDB 分片來分散寫入負載
2. **讀寫分離**：將讀操作引導到從節點
3. **緩存策略**：減少對熱點資料的直接寫入
4. **異步處理**：將部分操作改為異步執行