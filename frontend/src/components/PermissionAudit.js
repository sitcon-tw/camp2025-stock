import { useState, useEffect } from "react";
import { getAvailableRoles, getUserRole, getMyPermissions } from "@/lib/api";
import { PERMISSIONS, ROLES, ROLE_PERMISSIONS } from "@/contexts/PermissionContext";

/**
 * 權限審查工具組件
 * 用於審查和管理系統權限
 */
export const PermissionAudit = ({ token }) => {
    const [auditData, setAuditData] = useState({
        currentPermissions: [],
        currentRole: null,
        availableRoles: [],
        permissionMatrix: {},
        inconsistencies: [],
    });
    const [loading, setLoading] = useState(true);
    const [selectedTab, setSelectedTab] = useState("overview");

    useEffect(() => {
        fetchAuditData();
    }, [token]);

    const fetchAuditData = async () => {
        try {
            setLoading(true);
            
            // 並行獲取資料
            const [permissionResponse, rolesResponse] = await Promise.all([
                getMyPermissions(token),
                getAvailableRoles(token),
            ]);

            // 建立權限矩陣
            const matrix = buildPermissionMatrix(rolesResponse.roles || []);
            
            // 檢查不一致性
            const inconsistencies = checkInconsistencies(
                permissionResponse.permissions || [],
                permissionResponse.role,
                matrix
            );

            setAuditData({
                currentPermissions: permissionResponse.permissions || [],
                currentRole: permissionResponse.role,
                availableRoles: rolesResponse.roles || [],
                permissionMatrix: matrix,
                inconsistencies,
            });
        } catch (error) {
            console.error("Failed to fetch audit data:", error);
        } finally {
            setLoading(false);
        }
    };

    const buildPermissionMatrix = (roles) => {
        const matrix = {};
        roles.forEach(role => {
            matrix[role.name] = role.permissions || [];
        });
        return matrix;
    };

    const checkInconsistencies = (userPermissions, userRole, matrix) => {
        const issues = [];
        
        // 檢查是否有權限不符合角色
        const expectedPermissions = matrix[userRole] || [];
        
        // 缺少的權限
        const missingPermissions = expectedPermissions.filter(
            perm => !userPermissions.includes(perm)
        );
        
        // 多餘的權限
        const extraPermissions = userPermissions.filter(
            perm => !expectedPermissions.includes(perm)
        );

        if (missingPermissions.length > 0) {
            issues.push({
                type: "missing",
                severity: "warning",
                message: `角色 ${userRole} 缺少權限: ${missingPermissions.join(", ")}`,
                permissions: missingPermissions,
            });
        }

        if (extraPermissions.length > 0) {
            issues.push({
                type: "extra",
                severity: "info",
                message: `角色 ${userRole} 有額外權限: ${extraPermissions.join(", ")}`,
                permissions: extraPermissions,
            });
        }

        return issues;
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="text-lg text-gray-600">載入審查資料中...</div>
            </div>
        );
    }

    return (
        <div className="bg-[#1A325F] rounded-lg shadow-lg border border-[#294565]">
            {/* 頁簽導航 */}
            <div className="border-b border-[#294565]">
                <nav className="flex space-x-8 px-6">
                    {[
                        { id: "overview", label: "概覽" },
                        { id: "permissions", label: "權限詳情" },
                        { id: "matrix", label: "權限矩陣" },
                        { id: "audit", label: "審查報告" },
                    ].map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setSelectedTab(tab.id)}
                            className={`py-4 px-1 border-b-2 font-medium text-sm ${
                                selectedTab === tab.id
                                    ? "border-[#469FD2] text-[#92cbf4]"
                                    : "border-transparent text-[#557797] hover:text-[#92cbf4]"
                            }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </nav>
            </div>

            {/* 內容區域 */}
            <div className="p-6">
                {selectedTab === "overview" && (
                    <OverviewTab auditData={auditData} onRefresh={fetchAuditData} />
                )}
                {selectedTab === "permissions" && (
                    <PermissionsTab auditData={auditData} />
                )}
                {selectedTab === "matrix" && (
                    <MatrixTab auditData={auditData} />
                )}
                {selectedTab === "audit" && (
                    <AuditTab auditData={auditData} />
                )}
            </div>
        </div>
    );
};

/**
 * 概覽頁簽
 */
const OverviewTab = ({ auditData, onRefresh }) => (
    <div className="space-y-6">
        <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-[#92cbf4]">權限系統概覽</h2>
            <button
                onClick={onRefresh}
                className="bg-[#469FD2] text-white px-4 py-2 rounded hover:bg-[#5BAEE3]"
            >
                重新整理
            </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* 目前角色 */}
            <div className="bg-blue-600/20 p-4 rounded-lg border border-blue-500/30">
                <h3 className="font-semibold text-blue-400">目前角色</h3>
                <p className="text-2xl font-bold text-blue-300">
                    {auditData.currentRole || "未知"}
                </p>
            </div>

            {/* 權限數量 */}
            <div className="bg-green-600/20 p-4 rounded-lg border border-green-500/30">
                <h3 className="font-semibold text-green-400">擁有權限</h3>
                <p className="text-2xl font-bold text-green-300">
                    {auditData.currentPermissions.length}
                </p>
            </div>

            {/* 問題數量 */}
            <div className="bg-yellow-600/20 p-4 rounded-lg border border-yellow-500/30">
                <h3 className="font-semibold text-yellow-400">發現問題</h3>
                <p className="text-2xl font-bold text-yellow-300">
                    {auditData.inconsistencies.length}
                </p>
            </div>
        </div>

        {/* 快速問題摘要 */}
        {auditData.inconsistencies.length > 0 && (
            <div className="bg-yellow-600/20 border border-yellow-500/30 rounded-lg p-4">
                <h3 className="font-semibold text-yellow-400 mb-2">⚠️ 發現的問題</h3>
                <ul className="space-y-1">
                    {auditData.inconsistencies.slice(0, 3).map((issue, index) => (
                        <li key={index} className="text-yellow-300 text-sm">
                            • {issue.message}
                        </li>
                    ))}
                    {auditData.inconsistencies.length > 3 && (
                        <li className="text-yellow-300 text-sm">
                            還有 {auditData.inconsistencies.length - 3} 個問題...
                        </li>
                    )}
                </ul>
            </div>
        )}
    </div>
);

/**
 * 權限詳情頁簽
 */
const PermissionsTab = ({ auditData }) => (
    <div className="space-y-6">
        <h2 className="text-2xl font-bold text-[#92cbf4]">權限詳情</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 擁有的權限 */}
            <div>
                <h3 className="text-lg font-semibold text-[#92cbf4] mb-4">
                    擁有的權限 ({auditData.currentPermissions.length})
                </h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                    {auditData.currentPermissions.map(permission => (
                        <div key={permission} className="flex items-center p-2 bg-green-600/20 rounded border border-green-500/30">
                            <span className="text-green-400">✓</span>
                            <span className="ml-2 text-sm text-green-300">{permission}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* 所有可用權限 */}
            <div>
                <h3 className="text-lg font-semibold text-[#92cbf4] mb-4">所有系統權限</h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                    {Object.values(PERMISSIONS).map(permission => (
                        <div key={permission} className={`flex items-center p-2 rounded border ${
                            auditData.currentPermissions.includes(permission)
                                ? "bg-green-600/20 border-green-500/30"
                                : "bg-[#0f203e] border-[#294565]"
                        }`}>
                            <span className={
                                auditData.currentPermissions.includes(permission)
                                    ? "text-green-400"
                                    : "text-[#557797]"
                            }>
                                {auditData.currentPermissions.includes(permission) ? "✓" : "○"}
                            </span>
                            <span className={`ml-2 text-sm ${
                                auditData.currentPermissions.includes(permission)
                                    ? "text-green-300"
                                    : "text-[#7BC2E6]"
                            }`}>{permission}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    </div>
);

/**
 * 權限矩陣頁簽
 */
const MatrixTab = ({ auditData }) => (
    <div className="space-y-6">
        <h2 className="text-2xl font-bold text-[#92cbf4]">角色權限矩陣</h2>
        
        <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-[#294565]">
                <thead className="bg-[#0f203e]">
                    <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-[#7BC2E6] uppercase tracking-wider">
                            權限
                        </th>
                        {Object.keys(auditData.permissionMatrix).map(role => (
                            <th key={role} className="px-6 py-3 text-left text-xs font-medium text-[#7BC2E6] uppercase tracking-wider">
                                {role}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody className="bg-[#1A325F] divide-y divide-[#294565]">
                    {Object.values(PERMISSIONS).map(permission => (
                        <tr key={permission}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-[#92cbf4]">
                                {permission}
                            </td>
                            {Object.entries(auditData.permissionMatrix).map(([role, permissions]) => (
                                <td key={role} className="px-6 py-4 whitespace-nowrap text-sm text-[#7BC2E6]">
                                    {permissions.includes(permission) ? (
                                        <span className="text-green-400">✓</span>
                                    ) : (
                                        <span className="text-[#557797]">—</span>
                                    )}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    </div>
);

/**
 * 審查報告頁簽
 */
const AuditTab = ({ auditData }) => (
    <div className="space-y-6">
        <h2 className="text-2xl font-bold text-[#92cbf4]">審查報告</h2>
        
        {auditData.inconsistencies.length === 0 ? (
            <div className="bg-green-600/20 border border-green-500/30 rounded-lg p-4">
                <div className="flex items-center">
                    <span className="text-green-400 text-xl mr-2">✓</span>
                    <span className="text-green-300 font-semibold">
                        權限設定正常，未發現問題
                    </span>
                </div>
            </div>
        ) : (
            <div className="space-y-4">
                {auditData.inconsistencies.map((issue, index) => (
                    <div key={index} className={`border rounded-lg p-4 ${
                        issue.severity === "warning" 
                            ? "bg-yellow-600/20 border-yellow-500/30"
                            : "bg-blue-600/20 border-blue-500/30"
                    }`}>
                        <div className="flex items-start">
                            <span className={`text-xl mr-2 ${
                                issue.severity === "warning" 
                                    ? "text-yellow-400" 
                                    : "text-blue-400"
                            }`}>
                                {issue.severity === "warning" ? "⚠️" : "ℹ️"}
                            </span>
                            <div>
                                <p className={`font-semibold ${
                                    issue.severity === "warning" 
                                        ? "text-yellow-300" 
                                        : "text-blue-300"
                                }`}>
                                    {issue.type === "missing" ? "缺少權限" : "額外權限"}
                                </p>
                                <p className={`text-sm ${
                                    issue.severity === "warning" 
                                        ? "text-yellow-200" 
                                        : "text-blue-200"
                                }`}>
                                    {issue.message}
                                </p>
                                <div className="mt-2">
                                    <span className="text-xs font-medium text-[#7BC2E6]">
                                        相關權限:
                                    </span>
                                    <div className="flex flex-wrap gap-1 mt-1">
                                        {issue.permissions.map(perm => (
                                            <span key={perm} className="inline-block bg-[#0f203e] text-[#92cbf4] text-xs px-2 py-1 rounded border border-[#294565]">
                                                {perm}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        )}
    </div>
);

export default PermissionAudit;