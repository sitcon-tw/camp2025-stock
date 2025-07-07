import { createContext, useContext, useEffect, useState } from "react";
import { usePermissions } from "@/hooks/usePermissions";

// 權限上下文
const PermissionContext = createContext();

/**
 * 權限提供者設定
 * 為整個應用提供權限狀態管理
 */
export const PermissionProvider = ({ children, token }) => {
    const permissionData = usePermissions(token);
    
    return (
        <PermissionContext.Provider value={permissionData}>
            {children}
        </PermissionContext.Provider>
    );
};

/**
 * 使用權限上下文的 Hook
 * 在設定中使用此 Hook 來獲取權限資訊
 */
export const usePermissionContext = () => {
    const context = useContext(PermissionContext);
    if (!context) {
        throw new Error('usePermissionContext must be used within a PermissionProvider');
    }
    return context;
};

/**
 * 權限設定常量
 * 定義系統中的所有權限
 */
export const PERMISSIONS = {
    // 基本權限
    VIEW_OWN_DATA: "view_own_data",
    TRADE_STOCKS: "trade_stocks", 
    TRANSFER_POINTS: "transfer_points",
    
    // 管理權限
    VIEW_ALL_USERS: "view_all_users",
    GIVE_POINTS: "give_points",
    CREATE_ANNOUNCEMENT: "create_announcement",
    
    // 系統管理權限
    MANAGE_USERS: "manage_users",
    MANAGE_MARKET: "manage_market",
    SYSTEM_ADMIN: "system_admin",
};

/**
 * 角色設定常量
 * 定義系統中的所有角色
 */
export const ROLES = {
    STUDENT: "student",
    POINT_MANAGER: "point_manager",
    ANNOUNCER: "announcer", 
    ADMIN: "admin",
};

/**
 * 權限組設定
 * 將相關權限組合在一起
 */
export const PERMISSION_GROUPS = {
    // 基本功能
    BASIC: [
        PERMISSIONS.VIEW_OWN_DATA,
        PERMISSIONS.TRADE_STOCKS,
        PERMISSIONS.TRANSFER_POINTS,
    ],
    
    // 用戶管理
    USER_MANAGEMENT: [
        PERMISSIONS.VIEW_ALL_USERS,
        PERMISSIONS.MANAGE_USERS,
    ],
    
    // 點數管理
    POINT_MANAGEMENT: [
        PERMISSIONS.GIVE_POINTS,
    ],
    
    // 公告管理
    ANNOUNCEMENT_MANAGEMENT: [
        PERMISSIONS.CREATE_ANNOUNCEMENT,
    ],
    
    // 市場管理
    MARKET_MANAGEMENT: [
        PERMISSIONS.MANAGE_MARKET,
    ],
    
    // 系統管理
    SYSTEM_MANAGEMENT: [
        PERMISSIONS.SYSTEM_ADMIN,
        PERMISSIONS.MANAGE_USERS,
        PERMISSIONS.MANAGE_MARKET,
    ],
};

/**
 * 角色權限映射
 * 定義每個角色對應的權限
 */
export const ROLE_PERMISSIONS = {
    [ROLES.STUDENT]: [
        PERMISSIONS.VIEW_OWN_DATA,
        PERMISSIONS.TRADE_STOCKS,
        PERMISSIONS.TRANSFER_POINTS,
    ],
    [ROLES.POINT_MANAGER]: [
        PERMISSIONS.VIEW_OWN_DATA,
        PERMISSIONS.TRADE_STOCKS,
        PERMISSIONS.TRANSFER_POINTS,
        PERMISSIONS.VIEW_ALL_USERS,
        PERMISSIONS.GIVE_POINTS,
    ],
    [ROLES.ANNOUNCER]: [
        PERMISSIONS.VIEW_OWN_DATA,
        PERMISSIONS.TRADE_STOCKS,
        PERMISSIONS.TRANSFER_POINTS,
        PERMISSIONS.VIEW_ALL_USERS,
        PERMISSIONS.CREATE_ANNOUNCEMENT,
    ],
    [ROLES.ADMIN]: [
        PERMISSIONS.VIEW_OWN_DATA,
        PERMISSIONS.TRADE_STOCKS,
        PERMISSIONS.TRANSFER_POINTS,
        PERMISSIONS.VIEW_ALL_USERS,
        PERMISSIONS.GIVE_POINTS,
        PERMISSIONS.CREATE_ANNOUNCEMENT,
        PERMISSIONS.MANAGE_USERS,
        PERMISSIONS.MANAGE_MARKET,
        PERMISSIONS.SYSTEM_ADMIN,
    ],
};

export default PermissionContext;