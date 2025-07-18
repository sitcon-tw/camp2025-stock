# SITCON Camp 2025 股票交易模擬腳本

這裡有兩個模擬腳本，用來驗證和演示股票交易系統的運作邏輯。

## 腳本說明

### 1. `validate_example.py` - 範例場景驗證器
**簡化版本，專門驗證你提供的具體範例**

這個腳本模擬你在描述中提到的精確場景：
- 3個使用者（A、B、C），每人初始100點
- A買3股，B買1股（各20元）
- A賣21元3股，B買25元3股，應該21元成交  
- 最終結算：股票以20元/股強制賣出
- 驗證總點數守恆（無通膨）

**預期結果：**
- A: 103點 (40 + 21×3)
- B: 97點 (80 - 21×3 + 20×4) 
- C: 100點 (未參與交易)
- 總計: 300點

### 2. `simulation_trading.py` - 完整交易模擬器  
**10人3隊的完整交易流程**

這個腳本模擬更完整的場景：
- 10個玩家分成3隊
- 包含範例場景 + 隨機交易
- 驗證點數轉帳、市場撮合、最終結算等功能
- 統計各隊伍表現

## 使用方法

### 前置條件
1. 確保後端服務運行在 `http://localhost:8000`
2. 管理員密碼設為 `admin123`（或修改腳本中的 `ADMIN_PASSWORD`）

### 執行腳本

```bash
# 進入後端目錄
cd backend

# 執行簡化版範例驗證
python test/validate_example.py

# 或執行完整模擬
python test/simulation_trading.py
```

## 範例驗證邏輯

根據你的描述，系統應該實作以下特性：

1. **點數守恆**: 總點數始終等於初始發放的總點數，不會有通膨或通縮
2. **公平交易**: 想玩的人可以交易獲利，不玩的人也不會吃虧
3. **市場撮合**: 買賣訂單按價格優先順序撮合
4. **最終結算**: 活動結束時，剩餘股票以固定價格強制賣出

## 驗證重點

✅ **初始狀態**: 每人100點，股票20元/股  
✅ **交易撮合**: 限價訂單正確撮合  
✅ **價格發現**: 市場價格反映供需  
✅ **最終結算**: 股票轉回點數  
✅ **點數守恆**: 總點數不變  

## 預期輸出示例

```
[15:30:15] 🎯 開始驗證範例場景
[15:30:15] ✅ 管理員登入成功
[15:30:16] ✅ 使用者 A 註冊成功
[15:30:16] ✅ 使用者 B 註冊成功  
[15:30:16] ✅ 使用者 C 註冊成功
...
[15:30:20] 📊 初始狀態 - 使用者狀態:
[15:30:20]    A: 100點 + 0股(0元) = 總資產100元
[15:30:20]    B: 100點 + 0股(0元) = 總資產100元
[15:30:20]    C: 100點 + 0股(0元) = 總資產100元
[15:30:20]    總計: 300點 (應為300點)
...
[15:30:25] 📊 最終結算後 - 使用者狀態:
[15:30:25]    A: 103點 + 0股(0元) = 總資產103元
[15:30:25]    B: 97點 + 0股(0元) = 總資產97元  
[15:30:25]    C: 100點 + 0股(0元) = 總資產100元
[15:30:25]    總計: 300點 (應為300點)
```

## 故障排除

如果腳本執行失敗：

1. **檢查後端服務**: 確保 `python main.py` 正在運行
2. **檢查管理員密碼**: 確保密碼正確
3. **檢查API端點**: 確保所有API都正常運作
4. **清理資料**: 可能需要清理之前的測試資料

## 自定義設定

你可以修改腳本中的常數：
- `INITIAL_POINTS`: 初始點數（預設100）
- `INITIAL_STOCK_PRICE`: 初始股價（預設20）
- `FINAL_SETTLEMENT_PRICE`: 最終結算價格（預設20）
- `ADMIN_PASSWORD`: 管理員密碼

這些腳本幫助驗證你的交易系統是否正確實作了"想玩的人可以玩，不玩的也不吃虧"的核心理念！
