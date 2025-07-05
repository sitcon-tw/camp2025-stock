import { useState, useEffect, useCallback, useRef } from "react";
import { getMyPermissions } from "@/lib/api";

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
            
            // 嘗試從 RBAC API 獲取權限
            try {
                const response = await getMyPermissions(token);
                if (response) {
                    setPermissions(response.permissions || []);
                    setRole(response.role || null);
                    hasInitializedRef.current = true;
                    return;
                }
            } catch (rbacError) {
                console.log("RBAC API failed, checking if admin token:", rbacError);
                
                // 如果 RBAC API 失敗，檢查是否為傳統管理員 token
                // 嘗試調用管理員 API 來驗證
                try {
                    // 使用管理員 stats API 來驗證 admin token
                    const adminResponse = await fetch(
                        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/admin/stats`,
                        {
                            headers: {
                                Authorization: `Bearer ${token}`,
                                "Content-Type": "application/json",
                            },
                        }
                    );
                    
                    if (adminResponse.ok) {
                        // 是有效的管理員 token，設置管理員權限
                        console.log("Admin token validated, setting admin permissions");
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
                } catch (adminError) {
                    console.error("Admin API also failed:", adminError);
                }
                
                // 兩個 API 都失敗，假設為學員角色並設置基本權限
                console.log("Both APIs failed, setting student role with basic permissions");
                setRole("student");
                setPermissions([
                    "view_own_data",
                    "trade_stocks", 
                    "transfer_points"
                ]);
                hasInitializedRef.current = true;
                return;
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