import { useState, useEffect } from "react";
import { PermissionGuard, AdminGuard, PermissionButton } from "./PermissionGuard";
import { PERMISSIONS, ROLES } from "@/contexts/PermissionContext";
import { usePermissions } from "@/hooks/usePermissions";

/**
 * 管理員儀表板組件
 * 使用權限驅動的 UI 控制
 */
export const AdminDashboard = ({ token }) => {
    const { permissions, role, loading, isAdmin } = usePermissions(token);
    
    if (loading) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="text-lg text-gray-600">載入權限中...</div>
            </div>
        );
    }

    if (!isAdmin()) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="text-lg text-red-600">權限不足：需要管理員權限</div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* 系統管理區塊 */}
            <PermissionGuard
                requiredPermission={PERMISSIONS.SYSTEM_ADMIN}
                token={token}
                fallback={
                    <div className="p-4 bg-gray-100 rounded-lg text-gray-500">
                        您沒有系統管理權限
                    </div>
                }
            >
                <SystemManagementSection token={token} />
            </PermissionGuard>

            {/* 用戶管理區塊 */}
            <PermissionGuard
                requiredPermissions={[PERMISSIONS.VIEW_ALL_USERS, PERMISSIONS.MANAGE_USERS]}
                token={token}
            >
                <UserManagementSection token={token} />
            </PermissionGuard>

            {/* 點數管理區塊 */}
            <PermissionGuard
                requiredPermission={PERMISSIONS.GIVE_POINTS}
                token={token}
            >
                <PointManagementSection token={token} />
            </PermissionGuard>

            {/* 公告管理區塊 */}
            <PermissionGuard
                requiredPermission={PERMISSIONS.CREATE_ANNOUNCEMENT}
                token={token}
            >
                <AnnouncementSection token={token} />
            </PermissionGuard>

            {/* 市場管理區塊 */}
            <PermissionGuard
                requiredPermission={PERMISSIONS.MANAGE_MARKET}
                token={token}
            >
                <MarketManagementSection token={token} />
            </PermissionGuard>
        </div>
    );
};

/**
 * 系統管理區塊
 */
const SystemManagementSection = ({ token }) => (
    <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4 text-red-600">🔧 系統管理</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <PermissionButton
                requiredPermission={PERMISSIONS.SYSTEM_ADMIN}
                token={token}
                className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
                onClick={() => console.log("重置所有資料")}
            >
                重置所有資料
            </PermissionButton>
            
            <PermissionButton
                requiredPermission={PERMISSIONS.SYSTEM_ADMIN}
                token={token}
                className="bg-orange-500 text-white px-4 py-2 rounded hover:bg-orange-600"
                onClick={() => console.log("強制結算")}
            >
                強制結算
            </PermissionButton>
        </div>
    </div>
);

/**
 * 用戶管理區塊
 */
const UserManagementSection = ({ token }) => (
    <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4 text-blue-600">👥 用戶管理</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <PermissionButton
                requiredPermission={PERMISSIONS.VIEW_ALL_USERS}
                token={token}
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                onClick={() => console.log("查看所有用戶")}
            >
                查看所有用戶
            </PermissionButton>
            
            <PermissionButton
                requiredPermission={PERMISSIONS.MANAGE_USERS}
                token={token}
                className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                onClick={() => console.log("管理用戶角色")}
            >
                管理用戶角色
            </PermissionButton>
            
            <PermissionButton
                requiredPermission={PERMISSIONS.VIEW_ALL_USERS}
                token={token}
                className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600"
                onClick={() => console.log("查看用戶統計")}
            >
                查看用戶統計
            </PermissionButton>
        </div>
    </div>
);

/**
 * 點數管理區塊
 */
const PointManagementSection = ({ token }) => (
    <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4 text-green-600">💰 點數管理</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <PermissionButton
                requiredPermission={PERMISSIONS.GIVE_POINTS}
                token={token}
                className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                onClick={() => console.log("發放點數")}
            >
                發放點數
            </PermissionButton>
            
            <PermissionButton
                requiredPermission={PERMISSIONS.GIVE_POINTS}
                token={token}
                className="bg-yellow-500 text-white px-4 py-2 rounded hover:bg-yellow-600"
                onClick={() => console.log("點數記錄")}
            >
                查看點數記錄
            </PermissionButton>
        </div>
    </div>
);

/**
 * 公告管理區塊
 */
const AnnouncementSection = ({ token }) => (
    <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4 text-purple-600">📢 公告管理</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <PermissionButton
                requiredPermission={PERMISSIONS.CREATE_ANNOUNCEMENT}
                token={token}
                className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600"
                onClick={() => console.log("發布公告")}
            >
                發布公告
            </PermissionButton>
            
            <PermissionButton
                requiredPermission={PERMISSIONS.CREATE_ANNOUNCEMENT}
                token={token}
                className="bg-indigo-500 text-white px-4 py-2 rounded hover:bg-indigo-600"
                onClick={() => console.log("管理公告")}
            >
                管理公告
            </PermissionButton>
        </div>
    </div>
);

/**
 * 市場管理區塊
 */
const MarketManagementSection = ({ token }) => (
    <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4 text-orange-600">📈 市場管理</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <PermissionButton
                requiredPermission={PERMISSIONS.MANAGE_MARKET}
                token={token}
                className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                onClick={() => console.log("開盤")}
            >
                手動開盤
            </PermissionButton>
            
            <PermissionButton
                requiredPermission={PERMISSIONS.MANAGE_MARKET}
                token={token}
                className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
                onClick={() => console.log("收盤")}
            >
                手動收盤
            </PermissionButton>
            
            <PermissionButton
                requiredPermission={PERMISSIONS.MANAGE_MARKET}
                token={token}
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                onClick={() => console.log("IPO管理")}
            >
                IPO 管理
            </PermissionButton>
        </div>
    </div>
);

export default AdminDashboard;