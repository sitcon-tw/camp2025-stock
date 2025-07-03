import { PERMISSIONS, ROLES, ROLE_PERMISSIONS } from "@/contexts/PermissionContext";

/**
 * 權限輔助工具
 * 提供權限相關的實用函數
 */

/**
 * 獲取角色的預期權限
 * @param {string} role - 角色名稱
 * @returns {string[]} - 權限列表
 */
export const getExpectedPermissions = (role) => {
    return ROLE_PERMISSIONS[role] || [];
};

/**
 * 檢查權限是否符合角色
 * @param {string[]} userPermissions - 使用者權限
 * @param {string} userRole - 使用者角色
 * @returns {Object} - 檢查結果
 */
export const validatePermissions = (userPermissions, userRole) => {
    const expectedPermissions = getExpectedPermissions(userRole);
    
    const missingPermissions = expectedPermissions.filter(
        perm => !userPermissions.includes(perm)
    );
    
    const extraPermissions = userPermissions.filter(
        perm => !expectedPermissions.includes(perm)
    );
    
    return {
        isValid: missingPermissions.length === 0 && extraPermissions.length === 0,
        missingPermissions,
        extraPermissions,
        expectedPermissions,
    };
};

/**
 * 格式化權限名稱為可讀文字
 * @param {string} permission - 權限名稱
 * @returns {string} - 格式化後的文字
 */
export const formatPermissionName = (permission) => {
    const permissionNames = {
        [PERMISSIONS.VIEW_OWN_DATA]: "查看個人資料",
        [PERMISSIONS.TRADE_STOCKS]: "股票交易",
        [PERMISSIONS.TRANSFER_POINTS]: "轉帳點數",
        [PERMISSIONS.VIEW_ALL_USERS]: "查看所有使用者",
        [PERMISSIONS.GIVE_POINTS]: "發放點數",
        [PERMISSIONS.CREATE_ANNOUNCEMENT]: "發布公告",
        [PERMISSIONS.MANAGE_USERS]: "管理使用者",
        [PERMISSIONS.MANAGE_MARKET]: "管理市場",
        [PERMISSIONS.SYSTEM_ADMIN]: "系統管理",
    };
    
    return permissionNames[permission] || permission;
};

/**
 * 格式化角色名稱為可讀文字
 * @param {string} role - 角色名稱
 * @returns {string} - 格式化後的文字
 */
export const formatRoleName = (role) => {
    const roleNames = {
        [ROLES.STUDENT]: "學員",
        [ROLES.POINT_MANAGER]: "點數管理員",
        [ROLES.ANNOUNCER]: "公告員",
        [ROLES.ADMIN]: "管理員",
    };
    
    return roleNames[role] || role;
};

/**
 * 獲取角色的層級
 * @param {string} role - 角色名稱
 * @returns {number} - 角色層級 (數字越大權限越高)
 */
export const getRoleLevel = (role) => {
    const roleLevels = {
        [ROLES.STUDENT]: 1,
        [ROLES.POINT_MANAGER]: 2,
        [ROLES.ANNOUNCER]: 2,
        [ROLES.ADMIN]: 4,
    };
    
    return roleLevels[role] || 0;
};

/**
 * 檢查角色是否有更高權限
 * @param {string} role1 - 角色1
 * @param {string} role2 - 角色2
 * @returns {boolean} - role1 是否比 role2 有更高權限
 */
export const hasHigherRole = (role1, role2) => {
    return getRoleLevel(role1) > getRoleLevel(role2);
};

/**
 * 獲取權限的功能分組
 * @param {string} permission - 權限名稱
 * @returns {string} - 功能分組
 */
export const getPermissionCategory = (permission) => {
    const categories = {
        [PERMISSIONS.VIEW_OWN_DATA]: "基本功能",
        [PERMISSIONS.TRADE_STOCKS]: "基本功能",
        [PERMISSIONS.TRANSFER_POINTS]: "基本功能",
        [PERMISSIONS.VIEW_ALL_USERS]: "用戶管理",
        [PERMISSIONS.MANAGE_USERS]: "用戶管理",
        [PERMISSIONS.GIVE_POINTS]: "點數管理",
        [PERMISSIONS.CREATE_ANNOUNCEMENT]: "公告管理",
        [PERMISSIONS.MANAGE_MARKET]: "市場管理",
        [PERMISSIONS.SYSTEM_ADMIN]: "系統管理",
    };
    
    return categories[permission] || "其他";
};

/**
 * 按分組整理權限
 * @param {string[]} permissions - 權限列表
 * @returns {Object} - 按分組整理的權限
 */
export const groupPermissions = (permissions) => {
    const grouped = {};
    
    permissions.forEach(permission => {
        const category = getPermissionCategory(permission);
        if (!grouped[category]) {
            grouped[category] = [];
        }
        grouped[category].push(permission);
    });
    
    return grouped;
};

/**
 * 生成權限摘要報告
 * @param {string[]} userPermissions - 使用者權限
 * @param {string} userRole - 使用者角色
 * @returns {Object} - 權限摘要報告
 */
export const generatePermissionSummary = (userPermissions, userRole) => {
    const validation = validatePermissions(userPermissions, userRole);
    const groupedPermissions = groupPermissions(userPermissions);
    
    return {
        role: {
            name: userRole,
            displayName: formatRoleName(userRole),
            level: getRoleLevel(userRole),
        },
        permissions: {
            total: userPermissions.length,
            byCategory: groupedPermissions,
            expected: validation.expectedPermissions.length,
        },
        validation,
        summary: {
            hasAllExpectedPermissions: validation.missingPermissions.length === 0,
            hasExtraPermissions: validation.extraPermissions.length > 0,
            complianceScore: Math.round(
                ((validation.expectedPermissions.length - validation.missingPermissions.length) / 
                 validation.expectedPermissions.length) * 100
            ),
        },
    };
};

/**
 * 權限審查建議
 * @param {Object} summary - 權限摘要
 * @returns {string[]} - 建議列表
 */
export const getPermissionRecommendations = (summary) => {
    const recommendations = [];
    
    if (summary.validation.missingPermissions.length > 0) {
        recommendations.push(
            `建議新增權限: ${summary.validation.missingPermissions.map(formatPermissionName).join(", ")}`
        );
    }
    
    if (summary.validation.extraPermissions.length > 0) {
        recommendations.push(
            `建議檢查額外權限: ${summary.validation.extraPermissions.map(formatPermissionName).join(", ")}`
        );
    }
    
    if (summary.summary.complianceScore < 100) {
        recommendations.push(
            `權限合規性僅 ${summary.summary.complianceScore}%，建議進行權限調整`
        );
    }
    
    if (recommendations.length === 0) {
        recommendations.push("權限配置符合角色要求，無需調整");
    }
    
    return recommendations;
};

export default {
    getExpectedPermissions,
    validatePermissions,
    formatPermissionName,
    formatRoleName,
    getRoleLevel,
    hasHigherRole,
    getPermissionCategory,
    groupPermissions,
    generatePermissionSummary,
    getPermissionRecommendations,
};