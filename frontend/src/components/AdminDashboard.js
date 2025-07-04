import { useState, useEffect } from "react";
import { PermissionGuard, AdminGuard, PermissionButton } from "./PermissionGuard";
import { PERMISSIONS, ROLES } from "@/contexts/PermissionContext";
import { usePermissions } from "@/hooks/usePermissions";
import { RoleManagement } from "./RoleManagement";
import { QuickRoleSetup } from "./QuickRoleSetup";
import { 
    givePoints, 
    createAnnouncement, 
    resetAllData, 
    forceSettlement, 
    openMarket, 
    closeMarket 
} from "@/lib/api";

/**
 * 管理員儀表板組件
 * 使用權限驅動的 UI 控制
 */
export const AdminDashboard = ({ token }) => {
    const { permissions, role, loading, isAdmin } = usePermissions(token);
    const [activeSection, setActiveSection] = useState("overview");
    const [notification, setNotification] = useState({ show: false, message: "", type: "info" });
    
    const [showPointsModal, setShowPointsModal] = useState(false);
    const [showAnnouncementModal, setShowAnnouncementModal] = useState(false);
    const [pointsForm, setPointsForm] = useState({ username: "", amount: "" });
    const [announcementForm, setAnnouncementForm] = useState({ title: "", message: "" });
    
    // 顯示通知
    const showNotification = (message, type = "info") => {
        setNotification({ show: true, message, type });
        setTimeout(() => setNotification({ show: false, message: "", type: "info" }), 3000);
    };
    
    // 發放點數
    const handleGivePoints = async () => {
        try {
            await givePoints(token, pointsForm.username, "user", parseInt(pointsForm.amount));
            showNotification(`成功發放 ${pointsForm.amount} 點給 ${pointsForm.username}`, 'success');
            setShowPointsModal(false);
            setPointsForm({ username: "", amount: "" });
        } catch (error) {
            showNotification(`發放點數失敗: ${error.message}`, 'error');
        }
    };
    
    // 發布公告
    const handleCreateAnnouncement = async () => {
        try {
            await createAnnouncement(token, announcementForm.title, announcementForm.message, true);
            showNotification('公告已成功發布', 'success');
            setShowAnnouncementModal(false);
            setAnnouncementForm({ title: "", message: "" });
        } catch (error) {
            showNotification(`發布公告失敗: ${error.message}`, 'error');
        }
    };
    
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
            {/* 通知提示 */}
            {notification.show && (
                <div className={`p-4 rounded-lg border ${
                    notification.type === 'success' ? 'bg-green-600/20 border-green-500/30 text-green-400' :
                    notification.type === 'error' ? 'bg-red-600/20 border-red-500/30 text-red-400' :
                    'bg-blue-600/20 border-blue-500/30 text-blue-400'
                }`}>
                    {notification.message}
                </div>
            )}
            
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
                            <SystemManagementSection token={token} showNotification={showNotification} />
                        </PermissionGuard>
                    )}
                </div>
            </div>
            
            {/* 發放點數模態框 */}
            {showPointsModal && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-[#1A325F] p-6 rounded-lg border border-[#294565] max-w-md w-full mx-4">
                    <h3 className="text-lg font-bold text-[#92cbf4] mb-4">💰 發放點數</h3>
                    <div className="space-y-4">
                        <input
                            type="text"
                            placeholder="使用者名稱"
                            value={pointsForm.username}
                            onChange={(e) => setPointsForm({...pointsForm, username: e.target.value})}
                            className="w-full px-3 py-2 bg-[#0f203e] border border-[#294565] rounded text-white"
                        />
                        <input
                            type="number"
                            placeholder="點數數量"
                            value={pointsForm.amount}
                            onChange={(e) => setPointsForm({...pointsForm, amount: e.target.value})}
                            className="w-full px-3 py-2 bg-[#0f203e] border border-[#294565] rounded text-white"
                        />
                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowPointsModal(false)}
                                className="flex-1 px-4 py-2 bg-[#294565] text-[#92cbf4] rounded hover:bg-[#1A325F]"
                            >
                                取消
                            </button>
                            <button
                                onClick={handleGivePoints}
                                disabled={!pointsForm.username || !pointsForm.amount}
                                className="flex-1 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                            >
                                發放
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        )}
        
        {/* 發布公告模態框 */}
        {showAnnouncementModal && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-[#1A325F] p-6 rounded-lg border border-[#294565] max-w-md w-full mx-4">
                    <h3 className="text-lg font-bold text-[#92cbf4] mb-4">📢 發布公告</h3>
                    <div className="space-y-4">
                        <input
                            type="text"
                            placeholder="公告標題"
                            value={announcementForm.title}
                            onChange={(e) => setAnnouncementForm({...announcementForm, title: e.target.value})}
                            className="w-full px-3 py-2 bg-[#0f203e] border border-[#294565] rounded text-white"
                        />
                        <textarea
                            placeholder="公告內容"
                            value={announcementForm.message}
                            onChange={(e) => setAnnouncementForm({...announcementForm, message: e.target.value})}
                            rows={4}
                            className="w-full px-3 py-2 bg-[#0f203e] border border-[#294565] rounded text-white"
                        />
                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowAnnouncementModal(false)}
                                className="flex-1 px-4 py-2 bg-[#294565] text-[#92cbf4] rounded hover:bg-[#1A325F]"
                            >
                                取消
                            </button>
                            <button
                                onClick={handleCreateAnnouncement}
                                disabled={!announcementForm.title || !announcementForm.message}
                                className="flex-1 px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
                            >
                                發布
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            )}
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
                <PointManagementSection 
                    token={token} 
                    onGivePoints={() => setShowPointsModal(true)}
                    showNotification={showNotification} 
                />
            </PermissionGuard>

            {/* 公告管理區塊 */}
            <PermissionGuard requiredPermission={PERMISSIONS.CREATE_ANNOUNCEMENT} token={token}>
                <AnnouncementSection 
                    token={token} 
                    onCreateAnnouncement={() => setShowAnnouncementModal(true)}
                    showNotification={showNotification}
                />
            </PermissionGuard>

            {/* 市場管理區塊 */}
            <PermissionGuard requiredPermission={PERMISSIONS.MANAGE_MARKET} token={token}>
                <MarketManagementSection token={token} showNotification={showNotification} />
            </PermissionGuard>
        </div>
    </div>
);

/**
 * 系統管理區塊
 */
const SystemManagementSection = ({ token, showNotification }) => (
    <div className="bg-[#1A325F] p-6 rounded-lg shadow border border-[#294565]">
        <h2 className="text-xl font-bold mb-4 text-red-400">🔧 系統管理</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <PermissionButton
                requiredPermission={PERMISSIONS.SYSTEM_ADMIN}
                token={token}
                className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
                onClick={async () => {
                    if (confirm('確定要重置所有資料嗎？這個操作不可復原！')) {
                        try {
                            await resetAllData(token);
                            showNotification('所有資料已成功重置', 'success');
                        } catch (error) {
                            showNotification(`重置失敗: ${error.message}`, 'error');
                        }
                    }
                }}
            >
                重置所有資料
            </PermissionButton>
            
            <PermissionButton
                requiredPermission={PERMISSIONS.SYSTEM_ADMIN}
                token={token}
                className="bg-orange-500 text-white px-4 py-2 rounded hover:bg-orange-600"
                onClick={async () => {
                    if (confirm('確定要強制結算嗎？')) {
                        try {
                            await forceSettlement(token);
                            showNotification('強制結算已完成', 'success');
                        } catch (error) {
                            showNotification(`強制結算失敗: ${error.message}`, 'error');
                        }
                    }
                }}
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
const PointManagementSection = ({ token, onGivePoints, showNotification }) => (
    <div className="bg-[#1A325F] p-6 rounded-lg shadow border border-[#294565]">
        <h2 className="text-xl font-bold mb-4 text-green-400">💰 點數管理</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <PermissionButton
                requiredPermission={PERMISSIONS.GIVE_POINTS}
                token={token}
                className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                onClick={onGivePoints}
            >
                發放點數
            </PermissionButton>
            
            <PermissionButton
                requiredPermission={PERMISSIONS.GIVE_POINTS}
                token={token}
                className="bg-yellow-500 text-white px-4 py-2 rounded hover:bg-yellow-600"
                onClick={() => showNotification('點數記錄功能尚未實作', 'info')}
            >
                查看點數記錄
            </PermissionButton>
        </div>
    </div>
);

/**
 * 公告管理區塊
 */
const AnnouncementSection = ({ token, onCreateAnnouncement, showNotification }) => (
    <div className="bg-[#1A325F] p-6 rounded-lg shadow border border-[#294565]">
        <h2 className="text-xl font-bold mb-4 text-purple-400">📢 公告管理</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <PermissionButton
                requiredPermission={PERMISSIONS.CREATE_ANNOUNCEMENT}
                token={token}
                className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600"
                onClick={onCreateAnnouncement}
            >
                發布公告
            </PermissionButton>
            
            <PermissionButton
                requiredPermission={PERMISSIONS.CREATE_ANNOUNCEMENT}
                token={token}
                className="bg-indigo-500 text-white px-4 py-2 rounded hover:bg-indigo-600"
                onClick={() => showNotification('公告管理功能尚未實作', 'info')}
            >
                管理公告
            </PermissionButton>
        </div>
    </div>
);

/**
 * 市場管理區塊
 */
const MarketManagementSection = ({ token, showNotification }) => (
    <div className="bg-[#1A325F] p-6 rounded-lg shadow border border-[#294565]">
        <h2 className="text-xl font-bold mb-4 text-orange-400">📈 市場管理</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <PermissionButton
                requiredPermission={PERMISSIONS.MANAGE_MARKET}
                token={token}
                className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                onClick={async () => {
                    try {
                        await openMarket(token);
                        showNotification('市場已開盤', 'success');
                    } catch (error) {
                        showNotification(`開盤失敗: ${error.message}`, 'error');
                    }
                }}
            >
                手動開盤
            </PermissionButton>
            
            <PermissionButton
                requiredPermission={PERMISSIONS.MANAGE_MARKET}
                token={token}
                className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
                onClick={async () => {
                    try {
                        await closeMarket(token);
                        showNotification('市場已收盤', 'success');
                    } catch (error) {
                        showNotification(`收盤失敗: ${error.message}`, 'error');
                    }
                }}
            >
                手動收盤
            </PermissionButton>
            
            <PermissionButton
                requiredPermission={PERMISSIONS.MANAGE_MARKET}
                token={token}
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                onClick={() => showNotification('IPO管理功能尚未實作', 'info')}
            >
                IPO 管理
            </PermissionButton>
        </div>
    </div>
);

export default AdminDashboard;