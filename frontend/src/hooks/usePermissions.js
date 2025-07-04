import { useState, useEffect, useCallback } from "react";
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

    const fetchPermissions = useCallback(async () => {
        if (!token) {
            setLoading(false);
            setPermissions([]);
            setRole(null);
            return;
        }

        try {
            setLoading(true);
            setError(null);
            
            // 嘗試從 RBAC API 獲取權限
            try {
                const response = await getMyPermissions(token);
                if (response) {
                    setPermissions(response.permissions || []);
                    setRole(response.role || null);
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
                        return;
                    }
                } catch (adminError) {
                    console.error("Admin API also failed:", adminError);
                }
                
                // 兩個 API 都失敗，重新拋出原始錯誤
                throw rbacError;
            }
        } catch (err) {
            console.error("Failed to fetch permissions:", err);
            setError(err.message);
            setPermissions([]);
            setRole(null);
        } finally {
            setLoading(false);
        }
    }, [token]);

    useEffect(() => {
        fetchPermissions();
    }, [fetchPermissions]);

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