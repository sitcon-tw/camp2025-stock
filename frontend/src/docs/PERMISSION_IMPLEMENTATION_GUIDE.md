# 權限系統實作指南

## 📋 概述

本指南說明如何在前端應用中實作安全的權限驅動 UI 控制系統，包含立即改進、中期優化和長期維護策略。

## 🚀 第一階段：立即實施

### 1. 權限 API 集成

#### 新增的 API 函數 (`src/lib/api.js`)
```javascript
// 取得目前使用者的權限資訊
export async function getMyPermissions(token)

// 取得使用者角色資訊  
export async function getUserRole(token, userId)

// 檢查特定權限
export async function checkPermission(token, userId, permission)

// 取得可用角色列表
export async function getAvailableRoles(token)
```

#### 權限管理 Hook (`src/hooks/usePermissions.js`)
```javascript
const { permissions, role, loading, hasPermission, isAdmin } = usePermissions(token);
```

**主要功能：**
- 自動獲取和緩存權限資訊
- 提供權限檢查函數
- 處理載入狀態和錯誤

## 🛡️ 第二階段：中期改進

### 1. 權限守衛組件系統

#### PermissionGuard 組件 (`src/components/PermissionGuard.js`)
```javascript
// 基本權限檢查
<PermissionGuard requiredPermission="SYSTEM_ADMIN" token={token}>
    <AdminButton />
</PermissionGuard>

// 多權限檢查
<PermissionGuard 
    requiredPermissions={["GIVE_POINTS", "VIEW_ALL_USERS"]} 
    requireAll={false}
    token={token}
>
    <ManagementPanel />
</PermissionGuard>

// 角色檢查
<RoleGuard requiredRole="admin" token={token}>
    <AdminPanel />
</RoleGuard>
```

#### 權限按鈕組件
```javascript
<PermissionButton 
    requiredPermission="GIVE_POINTS"
    token={token}
    onClick={handleGivePoints}
    className="bg-green-500 text-white px-4 py-2 rounded"
>
    發放點數
</PermissionButton>
```

### 2. 權限上下文系統

#### PermissionContext (`src/contexts/PermissionContext.js`)
```javascript
// 應用層級的權限提供者
<PermissionProvider token={token}>
    <App />
</PermissionProvider>

// 在組件中使用
const { hasPermission, isAdmin } = usePermissionContext();
```

**預定義常量：**
- `PERMISSIONS` - 所有系統權限
- `ROLES` - 所有系統角色  
- `PERMISSION_GROUPS` - 權限分組
- `ROLE_PERMISSIONS` - 角色權限映射

## 🔍 第三階段：長期維護

### 1. 權限審查工具

#### PermissionAudit 組件 (`src/components/PermissionAudit.js`)
提供完整的權限審查界面：

- **概覽頁簽**：顯示目前角色、權限數量、發現的問題
- **權限詳情**：列出擁有的權限和所有可用權限
- **權限矩陣**：顯示所有角色的權限對應表
- **審查報告**：檢查權限不一致性和合規問題

### 2. 權限輔助工具

#### PermissionHelper (`src/utils/permissionHelper.js`)
```javascript
// 驗證權限是否符合角色
const validation = validatePermissions(userPermissions, userRole);

// 生成權限摘要報告
const summary = generatePermissionSummary(userPermissions, userRole);

// 獲取權限建議
const recommendations = getPermissionRecommendations(summary);

// 格式化權限和角色名稱
const displayName = formatPermissionName(permission);
const roleDisplayName = formatRoleName(role);
```

## 📝 使用範例

### 1. 替換現有管理員頁面

```javascript
// 舊版本 - 不安全
const isAdmin = localStorage.getItem("isAdmin");
if (isAdmin) {
    return <AdminPanel />;
}

// 新版本 - 安全
const { isAdmin, loading } = usePermissions(token);
if (loading) return <Loading />;
if (!isAdmin()) return <AccessDenied />;
return <AdminPanel />;
```

### 2. 動態功能選單

```javascript
function NavigationMenu({ token }) {
    const { hasPermission } = usePermissions(token);
    
    return (
        <nav>
            {hasPermission("VIEW_ALL_USERS") && (
                <NavItem href="/admin/users">用戶管理</NavItem>
            )}
            {hasPermission("GIVE_POINTS") && (
                <NavItem href="/admin/points">點數管理</NavItem>
            )}
            {hasPermission("CREATE_ANNOUNCEMENT") && (
                <NavItem href="/admin/announcements">公告管理</NavItem>
            )}
        </nav>
    );
}
```

### 3. 條件式功能區塊

```javascript
function Dashboard({ token }) {
    return (
        <div>
            <PermissionGuard requiredPermission="SYSTEM_ADMIN" token={token}>
                <DangerZone />
            </PermissionGuard>
            
            <PermissionGuard 
                requiredPermissions={["GIVE_POINTS", "VIEW_ALL_USERS"]} 
                token={token}
            >
                <ManagementTools />
            </PermissionGuard>
        </div>
    );
}
```

## 🔒 安全考量

### 1. 前端權限檢查限制
- **僅控制 UI 顯示**，不提供真正的安全保護
- **可能被開發者工具繞過**
- **主要目的是改善使用者體驗**

### 2. 真正的安全保護
- **後端 API 仍需完整權限驗證**
- **JWT Token 驗證不可省略**
- **所有重要操作都必須經過後端檢查**

### 3. 最佳實踐
- 定期使用權限審查工具檢查配置
- 監控異常的權限使用模式
- 記錄所有權限相關的操作

## 🚀 部署指南

### 1. 漸進式實施
1. **第一週**：實作權限 API 和基礎 Hook
2. **第二週**：替換關鍵頁面使用權限檢查
3. **第三週**：實施權限守衛組件
4. **第四週**：部署權限審查工具

### 2. 測試策略
- 測試各種權限組合的 UI 顯示
- 驗證權限變更後的即時更新
- 確認錯誤處理和載入狀態

### 3. 監控和維護
- 設置權限審查定期報告
- 監控權限 API 的使用情況
- 定期檢查權限配置的一致性

## 📚 相關文件

- `/src/hooks/usePermissions.js` - 權限管理 Hook
- `/src/components/PermissionGuard.js` - 權限守衛組件
- `/src/contexts/PermissionContext.js` - 權限上下文
- `/src/components/PermissionAudit.js` - 權限審查工具
- `/src/utils/permissionHelper.js` - 權限輔助函數
- `/src/app/admin/enhanced-page.js` - 增強版管理員頁面範例

## 🤝 貢獻指南

在修改權限相關代碼時，請確保：
1. 更新相關的權限常量定義
2. 測試所有權限組合的行為
3. 更新權限審查工具的檢查邏輯
4. 記錄權限變更的影響範圍

---

這個權限系統提供了完整的前端權限控制解決方案，同時保持了與後端安全機制的協調，確保系統的整體安全性。