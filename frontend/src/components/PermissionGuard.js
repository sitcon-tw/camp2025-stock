import { usePermissions } from "@/hooks/usePermissions";
import { twMerge } from "tailwind-merge";

/**
 * 權限守衛組件
 * 根據使用者權限決定是否渲染子組件
 */
export const PermissionGuard = ({
    children,
    requiredPermission,
    requiredPermissions = [],
    requireAll = false,
    requiredRole,
    token,
    fallback = null,
    showLoading = true,
    loadingComponent = (
        <div className="text-gray-500">檢查權限中...</div>
    ),
}) => {
    const {
        permissions,
        role,
        loading,
        hasPermission,
        hasAnyPermission,
        hasAllPermissions,
        hasRole,
    } = usePermissions(token);

    // 檢查權限邏輯
    const checkAccess = () => {
        // 檢查角色
        if (requiredRole && !hasRole(requiredRole)) {
            return false;
        }

        // 檢查單一權限
        if (
            requiredPermission &&
            !hasPermission(requiredPermission)
        ) {
            return false;
        }

        // 檢查多個權限
        if (requiredPermissions.length > 0) {
            if (requireAll) {
                return hasAllPermissions(requiredPermissions);
            } else {
                return hasAnyPermission(requiredPermissions);
            }
        }

        return true;
    };

    // 載入中
    if (loading && showLoading) {
        return loadingComponent;
    }

    // 如果沒有 requiredPermission，但 loading 剛結束且還沒有任何權限，稍等一下
    // 這可以解決 admin token fallback 的時序問題
    // 但是如果已經有 role 設定，即使 permissions 為空也不應該繼續載入
    if (!loading && permissions.length === 0 && !role && token) {
        return loadingComponent;
    }

    // 權限檢查
    if (!checkAccess()) {
        return fallback;
    }

    return children;
};

/**
 * 角色守衛組件
 * 根據使用者角色決定是否渲染子組件
 */
export const RoleGuard = ({
    children,
    requiredRole,
    token,
    fallback = null,
    showLoading = true,
    loadingComponent = (
        <div className="text-gray-500">檢查權限中...</div>
    ),
}) => {
    return (
        <PermissionGuard
            requiredRole={requiredRole}
            token={token}
            fallback={fallback}
            showLoading={showLoading}
            loadingComponent={loadingComponent}
        >
            {children}
        </PermissionGuard>
    );
};

/**
 * 管理員守衛組件
 * 僅管理員可見
 */
export const AdminGuard = ({
    children,
    token,
    fallback = null,
    showLoading = true,
}) => {
    return (
        <RoleGuard
            requiredRole="admin"
            token={token}
            fallback={fallback}
            showLoading={showLoading}
        >
            {children}
        </RoleGuard>
    );
};

/**
 * 權限按鈕組件
 * 根據權限控制按鈕是否可用
 */
export const PermissionButton = ({
    children,
    requiredPermission,
    requiredPermissions = [],
    requireAll = false,
    requiredRole,
    token,
    disabled = false,
    className = "",
    disabledClassName = "opacity-50 cursor-not-allowed",
    onClick,
    ...props
}) => {
    const {
        hasPermission,
        hasAnyPermission,
        hasAllPermissions,
        hasRole,
        loading,
    } = usePermissions(token);

    const checkAccess = () => {
        if (requiredRole && !hasRole(requiredRole)) return false;
        if (requiredPermission && !hasPermission(requiredPermission))
            return false;
        if (requiredPermissions.length > 0) {
            return requireAll
                ? hasAllPermissions(requiredPermissions)
                : hasAnyPermission(requiredPermissions);
        }
        return true;
    };

    const hasAccess = checkAccess();
    const isDisabled = disabled || loading || !hasAccess;

    const handleClick = (e) => {
        if (isDisabled) {
            e.preventDefault();
            return;
        }
        if (onClick) {
            onClick(e);
        }
    };

    return (
        <button
            {...props}
            className={twMerge(
                "disabled:cursor-not-allowed!",
                className,
                isDisabled && disabledClassName,
            )}
            disabled={isDisabled}
            onClick={handleClick}
        >
            {children}
        </button>
    );
};

export default PermissionGuard;
