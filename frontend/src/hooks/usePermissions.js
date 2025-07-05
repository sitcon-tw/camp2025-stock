import { useState, useEffect, useCallback, useRef } from "react";
import { getMyPermissions } from "@/lib/api";

/**
 * 解析 JWT token payload
 * @param {string} token - JWT token
 * @returns {Object|null} - Decoded payload or null if invalid
 */
const parseJWTPayload = (token) => {
    try {
        const tokenParts = token.split('.');
        if (tokenParts.length === 3) {
            return JSON.parse(atob(tokenParts[1]));
        }
    } catch (error) {
        console.log("Failed to parse JWT token:", error);
    }
    return null;
};

/**
 * 檢查是否為傳統管理員 token (早期系統)
 * @param {Object} payload - JWT payload
 * @returns {boolean}
 */
const isLegacyAdminToken = (payload) => {
    if (!payload) return false;
    
    // 傳統 admin token 特徵：
    // - sub 是 'admin' 
    // - 沒有 telegram_id (因為是早期系統)
    // - 可能有 username='admin' 或 is_admin=true
    return (payload.sub === 'admin' || 
            payload.username === 'admin' || 
            payload.is_admin === true) &&
           !payload.telegram_id; // 確保不是 Telegram token
};

/**
 * 檢查是否為 Telegram 用戶 token (新系統)
 * @param {Object} payload - JWT payload  
 * @returns {boolean}
 */
const isUserToken = (payload) => {
    if (!payload) return false;
    
    // Telegram 用戶 token 特徵：
    // - 有 telegram_id
    // - 或者有 user_id 且不是 admin
    return payload.telegram_id || 
           (payload.user_id && payload.sub !== 'admin');
};

/**
 * 權限管理 Hook
 * 用於獲取和管理使用者權限
 */
export const usePermissions = (token) => {
    const [permissions, setPermissions] = useState([]);
    const [role, setRole] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const isFetchingRef = useRef(false);
    const hasInitializedRef = useRef(false);

    const fetchPermissions = useCallback(async () => {
        if (!token) {
            setLoading(false);
            setPermissions([]);
            setRole(null);
            hasInitializedRef.current = true;
            return;
        }

        // 防止多次同時執行
        if (isFetchingRef.current) {
            return;
        }

        isFetchingRef.current = true;

        try {
            setLoading(true);
            setError(null);
            
            // 解析 JWT token 
            const payload = parseJWTPayload(token);
            console.log("Token payload:", payload);
            
            // === 路徑1: 傳統 Admin 系統 (早期系統) ===
            if (isLegacyAdminToken(payload)) {
                console.log("=== LEGACY ADMIN PATH ===");
                console.log("Early admin system token detected");
                
                // 直接設置傳統管理員權限，不調用 RBAC API
                setRole("admin");
                setPermissions([
                    "view_own_data",
                    "trade_stocks", 
                    "transfer_points",
                    "view_all_users",
                    "give_points",
                    "create_announcement",
                    "manage_users",
                    "manage_market",
                    "system_admin"
                ]);
                hasInitializedRef.current = true;
                return;
            }
            
            // === 路徑2: Telegram + RBAC 系統 (新系統) ===
            console.log("=== TELEGRAM + RBAC PATH ===");
            console.log("Attempting RBAC API for Telegram user");
            
            try {
                const response = await getMyPermissions(token);
                if (response) {
                    console.log("RBAC API success:", response);
                    setPermissions(response.permissions || []);
                    setRole(response.role || null);
                    hasInitializedRef.current = true;
                    return;
                }
            } catch (rbacError) {
                console.log("RBAC API failed:", rbacError);
                
                // 如果是用戶 token 但 RBAC 失敗，設為學員
                if (isUserToken(payload)) {
                    console.log("User token but RBAC failed, setting as student");
                    setRole("student");
                    setPermissions([
                        "view_own_data",
                        "trade_stocks", 
                        "transfer_points"
                    ]);
                    hasInitializedRef.current = true;
                    return;
                }
                
                // 不是已知的 token 類型
                throw rbacError;
            }
        } catch (err) {
            console.error("Failed to fetch permissions:", err);
            setError(err.message);
            // 如果所有嘗試都失敗，設置為學員角色
            setRole("student");
            setPermissions([
                "view_own_data",
                "trade_stocks", 
                "transfer_points"
            ]);
            hasInitializedRef.current = true;
        } finally {
            setLoading(false);
            isFetchingRef.current = false;
        }
    }, [token]);

    useEffect(() => {
        // 當 token 改變時，重置初始化狀態
        hasInitializedRef.current = false;
        fetchPermissions();
    }, [token, fetchPermissions]);

    /**
     * 檢查是否有特定權限
     * @param {string} permission - 權限名稱
     * @returns {boolean} - 是否有權限
     */
    const hasPermission = useCallback(
        (permission) => {
            return permissions.includes(permission);
        },
        [permissions]
    );

    /**
     * 檢查是否有任一權限
     * @param {string[]} permissionList - 權限列表
     * @returns {boolean} - 是否有任一權限
     */
    const hasAnyPermission = useCallback(
        (permissionList) => {
            return permissionList.some(permission => permissions.includes(permission));
        },
        [permissions]
    );

    /**
     * 檢查是否有所有權限
     * @param {string[]} permissionList - 權限列表
     * @returns {boolean} - 是否有所有權限
     */
    const hasAllPermissions = useCallback(
        (permissionList) => {
            return permissionList.every(permission => permissions.includes(permission));
        },
        [permissions]
    );

    /**
     * 檢查是否有特定角色
     * @param {string} targetRole - 目標角色
     * @returns {boolean} - 是否有該角色
     */
    const hasRole = useCallback(
        (targetRole) => {
            return role === targetRole;
        },
        [role]
    );

    /**
     * 檢查是否為管理員
     * @returns {boolean} - 是否為管理員
     */
    const isAdmin = useCallback(() => {
        return role === "admin";
    }, [role]);

    /**
     * 重新獲取權限
     */
    const refreshPermissions = useCallback(() => {
        hasInitializedRef.current = false;
        fetchPermissions();
    }, [fetchPermissions]);

    return {
        permissions,
        role,
        loading,
        error,
        hasPermission,
        hasAnyPermission,
        hasAllPermissions,
        hasRole,
        isAdmin,
        refreshPermissions,
    };
};

export default usePermissions;