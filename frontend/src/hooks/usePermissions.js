import { getMyPermissions } from "@/lib/api";
import { useCallback, useEffect, useRef, useState } from "react";

// Global cache to store permissions data across all hook instances - SESSION ONLY
const permissionsCache = new Map();

// Track ongoing API requests to prevent duplicates
const ongoingRequests = new Map();

/**
 * Get cache key for a token
 */
const getCacheKey = (token) => {
    if (!token) return null;
    return token.slice(-8); // Use last 8 characters as cache key
};

/**
 * Get cached data from memory cache only (session-based)
 */
const getCachedData = (token) => {
    if (!token) return null;

    const cacheKey = getCacheKey(token);

    // Check memory cache only - no time expiration needed since it's session-only
    const memoryCache = permissionsCache.get(cacheKey);
    if (memoryCache) {
        return memoryCache.data;
    }

    return null;
};

/**
 * Store data in memory cache only (session-based)
 */
const setCachedData = (token, data) => {
    if (!token) return;

    const cacheKey = getCacheKey(token);

    // Store in memory cache only - no timestamp needed
    permissionsCache.set(cacheKey, {
        data,
    });
};

/**
 * Clear cached data for a token (memory only)
 */
const clearCachedData = (token) => {
    if (!token) return;

    const cacheKey = getCacheKey(token);

    // Clear memory cache only
    permissionsCache.delete(cacheKey);
};

/**
 * Clear all cached data (useful for logout or session reset)
 */
export const clearAllPermissionsCache = () => {
    // Clear memory cache only
    permissionsCache.clear();
    ongoingRequests.clear();

    console.log("Cleared all cached permissions for current session");
};

/**
 * 解析 JWT token payload
 * @param {string} token - JWT token
 * @returns {Object|null} - Decoded payload or null if invalid
 */
const parseJWTPayload = (token) => {
    try {
        const tokenParts = token.split(".");
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
    if (!payload) {
        console.log("No payload found");
        return false;
    }

    console.log("Checking legacy admin token:", {
        sub: payload.sub,
        username: payload.username,
        is_admin: payload.is_admin,
        telegram_id: payload.telegram_id,
        role: payload.role,
    });

    // 傳統 admin token 特徵：
    // - sub 是 'admin'
    // - 沒有 telegram_id (因為是早期系統)
    // - 可能有 username='admin' 或 is_admin=true
    const isAdmin =
        payload.sub === "admin" ||
        payload.username === "admin" ||
        payload.is_admin === true ||
        payload.role === "admin";
    const hasNoTelegram = !payload.telegram_id;

    console.log("Legacy admin check:", { isAdmin, hasNoTelegram });

    return isAdmin && hasNoTelegram;
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
    return (
        payload.telegram_id ||
        (payload.user_id && payload.sub !== "admin")
    );
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
    const currentTokenRef = useRef(null);

    // Initialize immediately from cache if available
    useEffect(() => {
        if (!token) {
            setLoading(false);
            setPermissions([]);
            setRole(null);
            hasInitializedRef.current = true;
            currentTokenRef.current = null;
            return;
        }

        // If token hasn't changed and we're already initialized, don't do anything
        if (
            token === currentTokenRef.current &&
            hasInitializedRef.current
        ) {
            return;
        }

        currentTokenRef.current = token;

        // Try to get from cache immediately
        const cachedData = getCachedData(token);
        if (cachedData) {
            setPermissions(cachedData.permissions || []);
            setRole(cachedData.role || null);
            setLoading(false);
            setError(null);
            hasInitializedRef.current = true;
            return;
        }

        // Check if it's a legacy admin token
        const payload = parseJWTPayload(token);
        if (isLegacyAdminToken(payload)) {
            const adminData = {
                permissions: [
                    "view_own_data",
                    "trade_stocks",
                    "transfer_points",
                    "view_all_users",
                    "give_points",
                    "create_announcement",
                    "manage_users",
                    "manage_market",
                    "system_admin",
                ],
                role: "admin",
            };
            setPermissions(adminData.permissions);
            setRole(adminData.role);
            setLoading(false);
            setError(null);
            hasInitializedRef.current = true;
            // Cache the admin data
            setCachedData(token, adminData);
            return;
        }

        // If no cache available, need to fetch
        setLoading(true);
        setError(null);
        hasInitializedRef.current = false;

        // Trigger fetch
        fetchPermissions();
    }, [token]);

    const fetchPermissions = useCallback(async () => {
        if (!token || hasInitializedRef.current) {
            return;
        }

        // Prevent duplicate requests
        if (isFetchingRef.current) {
            return;
        }

        const cacheKey = getCacheKey(token);
        if (ongoingRequests.has(cacheKey)) {
            console.log("Request already in progress for this token");
            return;
        }

        isFetchingRef.current = true;
        ongoingRequests.set(cacheKey, true);

        try {
            const payload = parseJWTPayload(token);

            try {
                const response = await getMyPermissions(token);
                if (response) {
                    console.log("RBAC API success:", response);
                    setPermissions(response.permissions || []);
                    setRole(response.role || null);
                    setLoading(false);
                    setError(null);

                    // Store in cache
                    setCachedData(token, response);
                    hasInitializedRef.current = true;
                    return;
                }
            } catch (rbacError) {
                console.log("RBAC API failed:", rbacError);

                // If it's a user token but RBAC failed, set as student
                if (isUserToken(payload)) {
                    console.log(
                        "User token but RBAC failed, setting as student",
                    );
                    const studentData = {
                        permissions: [
                            "view_own_data",
                            "trade_stocks",
                            "transfer_points",
                        ],
                        role: "student",
                    };
                    setRole(studentData.role);
                    setPermissions(studentData.permissions);
                    setLoading(false);
                    setError(null);
                    hasInitializedRef.current = true;
                    // Cache the student fallback
                    setCachedData(token, studentData);
                    return;
                }

                throw rbacError;
            }
        } catch (err) {
            console.error("Failed to fetch permissions:", err);
            setError(err.message);

            // Final fallback to student role
            const fallbackData = {
                permissions: [
                    "view_own_data",
                    "trade_stocks",
                    "transfer_points",
                ],
                role: "student",
            };
            setRole(fallbackData.role);
            setPermissions(fallbackData.permissions);
            setLoading(false);
            hasInitializedRef.current = true;
        } finally {
            isFetchingRef.current = false;
            ongoingRequests.delete(cacheKey);
        }
    }, [token]);

    /**
     * 檢查是否有特定權限
     * @param {string} permission - 權限名稱
     * @returns {boolean} - 是否有權限
     */
    const hasPermission = useCallback(
        (permission) => {
            return permissions.includes(permission);
        },
        [permissions],
    );

    /**
     * 檢查是否有任一權限
     * @param {string[]} permissionList - 權限列表
     * @returns {boolean} - 是否有任一權限
     */
    const hasAnyPermission = useCallback(
        (permissionList) => {
            return permissionList.some((permission) =>
                permissions.includes(permission),
            );
        },
        [permissions],
    );

    /**
     * 檢查是否有所有權限
     * @param {string[]} permissionList - 權限列表
     * @returns {boolean} - 是否有所有權限
     */
    const hasAllPermissions = useCallback(
        (permissionList) => {
            return permissionList.every((permission) =>
                permissions.includes(permission),
            );
        },
        [permissions],
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
        [role],
    );

    /**
     * 檢查是否為管理員
     * @returns {boolean} - 是否為管理員
     */
    const isAdmin = useCallback(() => {
        return role === "admin";
    }, [role]);

    /**
     * 重新獲取權限 (清除快取並重新請求)
     */
    const refreshPermissions = useCallback(() => {
        if (token) {
            clearCachedData(token);
        }
        hasInitializedRef.current = false;
        setLoading(true);
        fetchPermissions();
    }, [token, fetchPermissions]);

    /**
     * 清除當前用戶的權限快取
     */
    const clearCache = useCallback(() => {
        if (token) {
            clearCachedData(token);
        }
    }, [token]);

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
        clearCache,
    };
};

export default usePermissions;
