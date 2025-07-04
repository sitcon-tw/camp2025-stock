import { useState, useEffect } from "react";
import { PermissionGuard, AdminGuard, PermissionButton } from "./PermissionGuard";
import { PERMISSIONS, ROLES } from "@/contexts/PermissionContext";
import { usePermissions } from "@/hooks/usePermissions";
import { RoleManagement } from "./RoleManagement";
import { QuickRoleSetup } from "./QuickRoleSetup";

/**
 * 管理員儀表板組件
 * 使用權限驅動的 UI 控制
 */
export const AdminDashboard = ({ token }) => {
    const { permissions, role, loading, isAdmin } = usePermissions(token);
    const [activeSection, setActiveSection] = useState("overview");
    
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
            {/* 功能導航 */}
            <div className="bg-[#1A325F] rounded-lg shadow border border-[#294565]">
                <div className="border-b border-[#294565]">
                    <nav className="flex space-x-8 px-6">
                        {[
                            { id: "overview", label: "功能概覽", icon: "🏠" },
                            { id: "roles", label: "角色管理", icon: "👥", permission: PERMISSIONS.MANAGE_USERS },
                            { id: "system", label: "系統管理", icon: "⚙️", permission: PERMISSIONS.SYSTEM_ADMIN },
                        ].map(section => (
                            <PermissionGuard
                                key={section.id}
                                requiredPermission={section.permission}
                                token={token}
                                fallback={section.id === "overview" ? null : undefined}
                            >
                                <button
                                    onClick={() => setActiveSection(section.id)}
                                    className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                                        activeSection === section.id
                                            ? "border-[#469FD2] text-[#92cbf4]"
                                            : "border-transparent text-[#557797] hover:text-[#92cbf4]"
                                    }`}
                                >
                                    <span>{section.icon}</span>
                                    <span>{section.label}</span>
                                </button>
                            </PermissionGuard>
                        ))}
                    </nav>
                </div>

                <div className="p-6">
                    {activeSection === "overview" && <OverviewSection token={token} />}
                    {activeSection === "roles" && (
                        <PermissionGuard
                            requiredPermission={PERMISSIONS.MANAGE_USERS}
                            token={token}
                            fallback={<div className="text-red-600">權限不足：需要用戶管理權限</div>}
                        >
                            <div className="space-y-6">
                                <QuickRoleSetup token={token} />
                                <RoleManagement token={token} />
                            </div>
                        </PermissionGuard>
                    )}
                    {activeSection === "system" && (
                        <PermissionGuard
                            requiredPermission={PERMISSIONS.SYSTEM_ADMIN}
                            token={token}
                            fallback={<div className="text-red-600">權限不足：需要系統管理權限</div>}
                        >
                            <SystemManagementSection token={token} />
                        </PermissionGuard>
                    )}
                </div>
            </div>
        </div>
    );
};

/**
 * 功能概覽區塊
 */
const OverviewSection = ({ token }) => (
    <div className="space-y-6">
        <div>
            <h2 className="text-2xl font-bold text-[#92cbf4] mb-2">管理員功能概覽</h2>
            <p className="text-[#557797]">選擇上方頁簽來使用不同的管理功能</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* 角色管理卡片 */}
            <PermissionGuard requiredPermission={PERMISSIONS.MANAGE_USERS} token={token}>
                <div className="bg-blue-600/20 p-6 rounded-lg border border-blue-500/30">
                    <div className="flex items-center mb-4">
                        <span className="text-2xl mr-3">👥</span>
                        <h3 className="text-lg font-semibold text-blue-400">角色管理</h3>
                    </div>
                    <p className="text-blue-300 text-sm mb-4">
                        管理使用者角色和權限，將使用者從學員提升為管理員角色
                    </p>
                    <div className="text-xs text-blue-300">
                        • 查看所有使用者<br/>
                        • 變更使用者角色<br/>
                        • 權限狀態檢視
                    </div>
                </div>
            </PermissionGuard>

            {/* 系統管理卡片 */}
            <PermissionGuard requiredPermission={PERMISSIONS.SYSTEM_ADMIN} token={token}>
                <div className="bg-red-600/20 p-6 rounded-lg border border-red-500/30">
                    <div className="flex items-center mb-4">
                        <span className="text-2xl mr-3">⚙️</span>
                        <h3 className="text-lg font-semibold text-red-400">系統管理</h3>
                    </div>
                    <p className="text-red-300 text-sm mb-4">
                        危險操作區域，包含系統重置和強制結算功能
                    </p>
                    <div className="text-xs text-red-300">
                        • 重置所有資料<br/>
                        • 強制結算<br/>
                        • 系統設定
                    </div>
                </div>
            </PermissionGuard>

            {/* 點數管理卡片 */}
            <PermissionGuard requiredPermission={PERMISSIONS.GIVE_POINTS} token={token}>
                <div className="bg-green-600/20 p-6 rounded-lg border border-green-500/30">
                    <div className="flex items-center mb-4">
                        <span className="text-2xl mr-3">💰</span>
                        <h3 className="text-lg font-semibold text-green-400">點數管理</h3>
                    </div>
                    <p className="text-green-300 text-sm mb-4">
                        發放點數給使用者，查看點數交易記錄
                    </p>
                    <div className="text-xs text-green-300">
                        • 發放點數<br/>
                        • 查看記錄<br/>
                        • 點數統計
                    </div>
                </div>
            </PermissionGuard>
        </div>

        {/* 其他管理功能 */}
        <div className="space-y-6">
            {/* 點數管理區塊 */}
            <PermissionGuard requiredPermission={PERMISSIONS.GIVE_POINTS} token={token}>
                <PointManagementSection token={token} />
            </PermissionGuard>

            {/* 公告管理區塊 */}
            <PermissionGuard requiredPermission={PERMISSIONS.CREATE_ANNOUNCEMENT} token={token}>
                <AnnouncementSection token={token} />
            </PermissionGuard>

            {/* 市場管理區塊 */}
            <PermissionGuard requiredPermission={PERMISSIONS.MANAGE_MARKET} token={token}>
                <MarketManagementSection token={token} />
            </PermissionGuard>
        </div>
    </div>
);

/**
 * 系統管理區塊
 */
const SystemManagementSection = ({ token }) => (
    <div className="bg-[#1A325F] p-6 rounded-lg shadow border border-[#294565]">
        <h2 className="text-xl font-bold mb-4 text-red-400">🔧 系統管理</h2>
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
    <div className="bg-[#1A325F] p-6 rounded-lg shadow border border-[#294565]">
        <h2 className="text-xl font-bold mb-4 text-green-400">💰 點數管理</h2>
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
    <div className="bg-[#1A325F] p-6 rounded-lg shadow border border-[#294565]">
        <h2 className="text-xl font-bold mb-4 text-purple-400">📢 公告管理</h2>
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
    <div className="bg-[#1A325F] p-6 rounded-lg shadow border border-[#294565]">
        <h2 className="text-xl font-bold mb-4 text-orange-400">📈 市場管理</h2>
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