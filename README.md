<div align="center">

<img src="uwu.svg" width="200" alt="SITCON 喵券機 Logo">

# 🐱 SITCON 喵券機

**SITCON Camp 2025 點數交易系統**

<img width="1959" height="1000" alt="系統截圖" src="https://github.com/user-attachments/assets/e4892990-9447-49a4-a9f1-1acc427e3ffb" />

[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/SITCONCamp2025Bot)
[![Website](https://img.shields.io/badge/🌐_Website-Visit-585e70?style=for-the-badge)](https://t.me/SITCONCamp2025Bot)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-14+-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://mongodb.com)

</div>

---

## ✨ 專案簡介

SITCON 喵券機是專為 **SITCON Camp 2025** 設計的虛擬點數交易系統，結合了股票市場機制與遊戲化元素，讓營隊學員能夠體驗有趣的交易互動。

## 🚀 核心功能

| 模組 | 功能描述 |
|------|----------|
| 📈 **即時股價系統** | 股票即時報價、五檔掛單查詢、成交紀錄追蹤 |
| 🤖 **Telegram Bot** | 查詢點數、進行交易、參與互動遊戲 |
| 🌐 **Web 前端** | 股價走勢圖表、排行榜、管理員後台 |
| 🔐 **管理後台** | 用戶管理、點數發放、市場控制、公告發布 |
| 💰 **借貸系統** | 借款、還款、自動扣款機制 |
| ⚔️ **PvP 對戰** | 玩家間互動對決遊戲 |

## 🛠️ 技術堆疊

```
Frontend     →  Next.js 14+ / React / TailwindCSS
Backend      →  FastAPI / Python 3.12+ / Pydantic
Database     →  MongoDB
Bot          →  python-telegram-bot
DevOps       →  Docker / uv (Python Package Manager)
```

## 📁 專案架構

```
. 
├── 🎨 frontend/               # Next.js 前端應用
│   ├── src/                   # 原始碼
│   └── public/                # 靜態資源
│
├── ⚙️ backend/                # FastAPI 後端服務
│   ├── app/
│   │   ├── domain/            # DDD 領域層（實體、值物件、領域服務）
│   │   ├── application/       # DDD 應用層（用例、DTO）
│   │   ├── infrastructure/    # DDD 基礎設施層（Repository 實作）
│   │   ├── routers/           # API 路由控制器
│   │   ├── services/          # 業務邏輯層
│   │   ├── schemas/           # Pydantic 資料模型
│   │   └── core/              # 核心模組（DB、安全、例外處理）
│   ├── test/                  # 測試檔案
│   └── scripts/               # 工具腳本
│
└── 🤖 bot/                    # Telegram Bot
    ├── api/                   # Bot API 模組
    ├── bot/                   # Bot 核心邏輯
    └── utils/                 # 工具函式
```

> ⚠️ **Note**: 後端正在進行 DDD（Domain-Driven Design）架構重構中，`domain/`、`application/`、`infrastructure/` 為新架構，部分功能仍使用原有的 `routers/`、`services/`、`schemas/` 結構。

## 📡 API 端點總覽

### 🔓 公開 API（無需認證）

| Method | Endpoint | 說明 |
|--------|----------|------|
| `GET` | `/api/price/summary` | 股票即時報價摘要 |
| `GET` | `/api/price/depth` | 五檔掛單查詢 |
| `GET` | `/api/price/trades` | 最近成交紀錄 |
| `GET` | `/api/price/current` | 快速查詢目前股價 |
| `GET` | `/api/leaderboard` | 排行榜查詢 |
| `GET` | `/api/status` | 市場狀態查詢 |
| `GET` | `/api/stats` | 系統統計資訊 |

### 🔐 管理員 API（需 JWT 認證）

| Method | Endpoint | 說明 |
|--------|----------|------|
| `POST` | `/api/admin/login` | 管理員登入 |
| `GET` | `/api/admin/user` | 查詢使用者資產明細 |
| `POST` | `/api/admin/users/give-points` | 發放點數 |
| `POST` | `/api/admin/announcement` | 發布公告 |
| `POST` | `/api/admin/market/update` | 更新市場開放時間 |
| `POST` | `/api/admin/market/set-limit` | 設定漲跌限制 |

## 🏃‍♂️ 快速開始

### 環境需求

- Python 3.12+
- Node.js 18+
- MongoDB
- Docker (optional)

### 後端啟動

```bash
cd backend

# 使用 uv 安裝依賴
uv venv && uv sync

# 設定環境變數
cp .env.example .env
# 編輯 .env 填入正確設定值

# 啟動伺服器
uv run ./main.py
```

### 前端啟動

```bash
cd frontend

# 安裝依賴
pnpm install

# 開發模式
pnpm dev
```

### API 文件

啟動後端後，可透過以下位置存取 API 文件：

- 📚 **Swagger UI**: http://localhost:8000/docs
- 📖 **ReDoc**: http://localhost:8000/redoc
- 💚 **Health Check**: http://localhost:8000/health

## 👥 貢獻者

<a href="https://github.com/KoukeNeko"><img src="https://avatars.githubusercontent.com/u/111033412?v=4" width="50" height="50" alt="KoukeNeko" style="border-radius:50%"></a>
<a href="https://github.com/wolf-yuan-6115"><img src="https://avatars.githubusercontent.com/u/58245644?v=4" width="50" height="50" alt="wolf-yuan-6115" style="border-radius:50%"></a>
<a href="https://github.com/Dash2100"><img src="https://avatars.githubusercontent.com/u/87257550?v=4" width="50" height="50" alt="Dash2100" style="border-radius:50%"></a>
<a href="https://github.com/Edit-Mr"><img src="https://avatars.githubusercontent.com/u/61068739?v=4" width="50" height="50" alt="Edit-Mr" style="border-radius:50%"></a>

## 📖 使用教學

詳細操作說明請參考：[📈 SITC 股市交易指南](https://hackmd.io/@SITCON/ry4JQ7gGeg)

## 📄 授權

本專案為 SITCON Camp 2025 活動專案。

---

<div align="center">

Made with 💜 by SITCON Camp 2025 Team

</div>
