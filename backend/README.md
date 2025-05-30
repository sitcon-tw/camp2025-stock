# SITCON Camp 2025 點數系統 - 完整 API 實作

## 功能概述
-  實作了 [SITCON Camp 2025 RESTful API 規格書](https://hackmd.io/@SITCON/ryuqDN7zex)
-  使用 FastAPI 作為伺服器框架
-  使用 MongoDB 作為主要資料庫



## API Endpoints

#### 公開資料 API（不用登入）
1. **`GET /api/price/summary`** - 股票即時報價摘要
2. **`GET /api/price/depth`** - 五檔掛單查詢
3. **`GET /api/price/trades?limit=20`** - 最近成交紀錄
4. **`GET /api/leaderboard`** - 排行榜查詢
5. **`GET /api/status`** - 市場狀態查詢

#### 管理員後台 API（需要登入）
1. **`POST /api/admin/login`** - 管理員登入
2. **`GET /api/admin/user?user=XXX`** - 查詢使用者資產明細
3. **`POST /api/admin/users/give-points`** - 給予點數（可給個人/群組）
4. **`POST /api/admin/announcement`** - 發布公告
5. **`POST /api/admin/market/update`** - 更新市場開放時間
6. **`POST /api/admin/market/set-limit`** - 設定漲跌限制

#### 其他 API
1. **`GET /api/price/current`** - 快速查詢目前股價
2. **`GET /api/stats`** - 系統統計資訊
3. **`GET /api/admin/announcements`** - 取得公告列表
4. **`GET /api/admin/stats`** - 管理員系統統計

## 專案架構

```
app/
├── main.py                 # 入口
├── config.py               # 讀取 Config（.env）
├── schemas/
│   └── public.py           # 所有 API 的 Pydantic 模型
├── services/
│   ├── admin_service.py    # 管理員 API 邏輯
│   └── public_service.py   # 公開 API 邏輯
├── routers/
│   ├── admin.py            # 管理員 Route 控制器
│   └── public.py           # 公開 Route 控制器
└── core/
    ├── database.py         # 資料庫連線
    ├── security.py         # 安全認證
    └── exceptions.py       # 異常處理
```

## 測試

### 1. 安裝依賴

```bash
cd backend

# 使用 uv 創虛擬環境（如果不存在）
uv venv

# 同步並安裝所有依賴
uv sync

# 以開發模式安裝項目
uv pip install -e .
```

### 2. 設定環境變數

```bash
# 生成 .env.example 文件 (如果沒有)
python env_config.py --generate

# 重新命名 (在你填入正確的值之後)
mv .env.example .env

# 驗證 .env 文件
python check_config.py
```

### 3. 啟動 MongoDB

確保 MongoDB 服務正在執行：

```bash
# 使用 Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# 或使用本地安裝的 MongoDB
mongod --dbpath /path/to/data/directory
```

### 5. 打開伺服器

```bash
uv run ./main.py
```

### 6. API 文件

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康檢查**: http://localhost:8000/health

## API 測試使用
在專案的 `/test` 下方有 py 檔可以直接發 Request 測試

你也可以用下面的 curl 測試範例：

### 公開 API 測試（無需認證）

#### 查詢股票價格摘要
```bash
curl -X GET "http://localhost:8000/api/price/summary"
```

#### 查詢五檔報價
```bash
curl -X GET "http://localhost:8000/api/price/depth"
```

#### 查詢最近成交記錄
```bash
curl -X GET "http://localhost:8000/api/price/trades?limit=10"
```

#### 查詢排行榜
```bash
curl -X GET "http://localhost:8000/api/leaderboard"
```

#### 查詢市場狀態
```bash
curl -X GET "http://localhost:8000/api/status"
```

### 管理員 API 測試（需要認證）

#### 管理員登入 (先用密碼跟伺服器拿 JWT Token)
```bash
curl -X POST "http://localhost:8000/api/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"password": "管理員的密碼"}'
```

#### 查詢使用者資產
```bash
# 查詢所有使用者
curl -X GET "http://localhost:8000/api/admin/user" \
  -H "Authorization: Bearer JWT_TOKEN"

# 查詢特定使用者
curl -X GET "http://localhost:8000/api/admin/user?user=勞贖" \
  -H "Authorization: Bearer JWT_TOKEN"
```

#### 給予點數
```bash
# 給個人點數
curl -X POST "http://localhost:8000/api/admin/users/give-points" \
  -H "Authorization: Bearer JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "勞贖",
    "type": "user",
    "amount": 100
  }'

# 給群組點數
curl -X POST "http://localhost:8000/api/admin/users/give-points" \
  -H "Authorization: Bearer JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "第三小隊",
    "type": "group",
    "amount": 50
  }'
```