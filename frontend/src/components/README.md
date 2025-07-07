# Components 目錄結構

本目錄包含所有 React 組件，按功能分類組織。

## 目錄結構

```
components/
├── admin/          # 管理員相關組件
├── charts/         # 圖表相關組件
├── trading/        # 交易相關組件
├── ui/            # 通用 UI 組件
└── index.js       # 統一導出入口
```

## 組件分類

### 📊 Admin (`/admin`)
管理員後台相關組件：
- `AdminDashboard.js` - 管理員主控台
- `AnnouncementManagement.js` - 公告管理
- `PermissionAudit.js` - 權限審查
- `PermissionGuard.js` - 權限守衛和按鈕
- `QuickRoleSetup.js` - 快速角色設定
- `RoleManagement.js` - 角色管理
- `SystemConfig.js` - 系統設定

### 📈 Charts (`/charts`)
圖表和視覺化組件：
- `CandlestickChart.js` - K線圖
- `KLineChart.js` - K線圖表
- `StockChart.js` - 股票圖表

### 💹 Trading (`/trading`)
交易相關組件：
- `TradingHoursVisualizer.js` - 交易時間可視化
- `TradingTabs.js` - 交易頁簽

### 🎨 UI (`/ui`)
通用界面組件：
- `HeaderBar.js` - 頁面標題欄
- `Modal.js` + `Modal.css` - 模態對話框
- `NavBar.js` - 導航欄

## 使用方式

### 方式一：從分類目錄導入
```javascript
import { AdminDashboard, SystemConfig } from '@/components/admin';
import { StockChart } from '@/components/charts';
import { Modal } from '@/components/ui';
```

### 方式二：從根目錄導入（推薦）
```javascript
import { 
  AdminDashboard, 
  SystemConfig, 
  StockChart, 
  Modal 
} from '@/components';
```

## 維護指南

1. **新增組件**：根據功能將組件放入對應分類目錄
2. **更新 index.js**：在對應目錄的 index.js 中添加導出
3. **命名規範**：使用 PascalCase 命名組件文件
4. **依賴管理**：避免循環引用，UI 組件應該是最基礎層級

## 注意事項

- 所有組件都應該有清楚的職責分工
- UI 組件應該保持通用性，避免業務邏輯
- Admin 組件通常需要權限檢查
- Charts 組件應該專注於數據可視化
- Trading 組件處理交易相關的業務邏輯