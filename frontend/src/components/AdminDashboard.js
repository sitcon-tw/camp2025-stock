import { useState, useEffect } from "react";
import { PermissionGuard, AdminGuard, PermissionButton } from "./PermissionGuard";
import { PERMISSIONS, ROLES } from "@/contexts/PermissionContext";
import { usePermissions } from "@/hooks/usePermissions";
import { RoleManagement } from "./RoleManagement";
// import { QuickRoleSetup } from "./QuickRoleSetup";
import { AnnouncementManagement } from "./AnnouncementManagement";
import { 
    givePoints, 
    resetAllData, 
    forceSettlement, 
    openMarket, 
    closeMarket,
    getSystemStats,
    getAdminMarketStatus,
    getIpoStatus,
    getIpoDefaults,
    updateIpo,
    resetIpo,
    executeCallAuction,
    getTradingHours,
    updateMarketTimes,
    getTransferFeeConfig,
    updateTransferFeeConfig,
    getUserAssets,
    getTeams,
    setTradingLimit
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
    const [pointsForm, setPointsForm] = useState({ username: "", amount: "" });
    
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
    
    
    if (loading) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="text-lg text-gray-600">載入權限中...</div>
            </div>
        );
    }

    // 如果沒有 role 且有 token，繼續顯示載入中（可能在 fallback 驗證中）
    if (!role && token) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="text-lg text-gray-600">驗證權限中...</div>
            </div>
        );
    }

    // 檢查是否有管理權限（admin、point_manager、announcer 都可以訪問）
    const hasManagementAccess = isAdmin() || role === 'point_manager' || role === 'announcer';
    
    if (!hasManagementAccess) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="text-center">
                    <div className="text-lg text-red-600 mb-2">權限不足：需要管理相關權限</div>
                    <div className="text-sm text-gray-600">您的角色：{role}</div>
                    <div className="text-sm text-gray-600">允許的角色：admin、point_manager、announcer</div>
                </div>
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
                    {activeSection === "overview" && (
                        <OverviewSection 
                            token={token} 
                            setShowPointsModal={setShowPointsModal}
                            showNotification={showNotification}
                        />
                    )}
                    {activeSection === "roles" && (
                        <PermissionGuard
                            requiredPermission={PERMISSIONS.MANAGE_USERS}
                            token={token}
                            fallback={<div className="text-red-600">權限不足：需要用戶管理權限</div>}
                        >
                            <div className="space-y-6">
                                {/* <QuickRoleSetup token={token} /> */}
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
        </div>
    );
};

/**
 * 功能概覽區塊
 */
const OverviewSection = ({ token, setShowPointsModal, showNotification }) => (
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
                <AnnouncementManagement 
                    token={token} 
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
 * 市場管理區塊
 */
const MarketManagementSection = ({ token, showNotification }) => {
    const [marketStatus, setMarketStatus] = useState(null);
    const [ipoStatus, setIpoStatus] = useState(null);
    const [showIpoModal, setShowIpoModal] = useState(false);
    const [callAuctionLoading, setCallAuctionLoading] = useState(false);
    const [showTradingLimitModal, setShowTradingLimitModal] = useState(false);
    const [tradingLimitPercent, setTradingLimitPercent] = useState(10);
    const [ipoForm, setIpoForm] = useState({
        sharesRemaining: "",
        initialPrice: "",
    });

    // 獲取市場狀態
    useEffect(() => {
        const fetchMarketStatus = async () => {
            try {
                const status = await getAdminMarketStatus(token);
                setMarketStatus(status);
            } catch (error) {
                console.error("獲取市場狀態失敗:", error);
            }
        };

        const fetchIpoStatus = async () => {
            try {
                const status = await getIpoStatus(token);
                setIpoStatus(status);
            } catch (error) {
                console.error("獲取IPO狀態失敗:", error);
            }
        };

        fetchMarketStatus();
        fetchIpoStatus();
    }, [token]);

    // 執行集合競價
    const handleCallAuction = async () => {
        try {
            setCallAuctionLoading(true);
            const result = await executeCallAuction(token);

            if (result.success) {
                let message = result.message;

                // 如果有詳細統計，新增到通知中
                if (result.order_stats) {
                    const stats = result.order_stats;
                    const totalBuy = (stats.pending_buy || 0) + (stats.limit_buy || 0);
                    const totalSell = (stats.pending_sell || 0) + (stats.limit_sell || 0);
                    message += ` (處理了 ${totalBuy} 張買單、${totalSell} 張賣單)`;
                }

                showNotification(message, "success");
            } else {
                let errorMessage = result.message || "集合競價執行失敗";
                showNotification(errorMessage, "error");
            }
        } catch (error) {
            showNotification(`集合競價失敗: ${error.message}`, "error");
        } finally {
            setCallAuctionLoading(false);
        }
    };

    // 更新IPO
    const handleIpoUpdate = async () => {
        try {
            const sharesRemaining = ipoForm.sharesRemaining !== "" ? parseInt(ipoForm.sharesRemaining) : null;
            const initialPrice = ipoForm.initialPrice !== "" ? parseInt(ipoForm.initialPrice) : null;

            const result = await updateIpo(token, sharesRemaining, initialPrice);

            showNotification(result.message, "success");
            setShowIpoModal(false);
            setIpoForm({
                sharesRemaining: "",
                initialPrice: "",
            });

            // 重新取得IPO狀態
            const status = await getIpoStatus(token);
            setIpoStatus(status);
        } catch (error) {
            showNotification(`IPO更新失敗: ${error.message}`, "error");
        }
    };

    // 重置IPO
    const handleIpoReset = async () => {
        try {
            if (confirm('確定要重置IPO嗎？')) {
                const result = await resetIpo(token);
                showNotification(result.message, "success");

                // 重新取得IPO狀態
                const status = await getIpoStatus(token);
                setIpoStatus(status);
            }
        } catch (error) {
            showNotification(`IPO重置失敗: ${error.message}`, "error");
        }
    };

    // 設定交易限制
    const handleSetTradingLimit = async () => {
        try {
            await setTradingLimit(token, parseFloat(tradingLimitPercent));
            showNotification("交易限制設定成功！", "success");
            setShowTradingLimitModal(false);
        } catch (error) {
            showNotification(`設定交易限制失敗: ${error.message}`, "error");
        }
    };

    return (
        <div className="bg-[#1A325F] p-6 rounded-lg shadow border border-[#294565]">
            <h2 className="text-xl font-bold mb-4 text-orange-400">📈 市場管理</h2>

            {/* 市場狀態顯示 */}
            {marketStatus && (
                <div className="mb-6 p-4 rounded-lg bg-[#0f203e] border border-[#294565]">
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-[#7BC2E6]">市場狀態:</span>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                            marketStatus.is_open 
                                ? "bg-green-600 text-green-100" 
                                : "bg-red-600 text-red-100"
                        }`}>
                            {marketStatus.is_open ? "開盤中" : "已收盤"}
                        </span>
                    </div>
                    {marketStatus.last_updated && (
                        <div className="text-sm text-gray-400">
                            最後更新: {new Date(marketStatus.last_updated).toLocaleString("zh-TW")}
                        </div>
                    )}
                </div>
            )}

            {/* IPO狀態顯示 */}
            {ipoStatus && (
                <div className="mb-6 p-4 rounded-lg bg-[#0f203e] border border-[#294565]">
                    <h3 className="text-lg font-medium mb-2 text-[#7BC2E6]">IPO 狀態</h3>
                    <div className="grid grid-cols-3 gap-4 mb-4">
                        <div className="text-center">
                            <div className="text-lg font-bold text-white">
                                {ipoStatus.initialShares?.toLocaleString()}
                            </div>
                            <div className="text-xs text-gray-400">初始股數</div>
                        </div>
                        <div className="text-center">
                            <div className="text-lg font-bold text-orange-400">
                                {ipoStatus.sharesRemaining?.toLocaleString()}
                            </div>
                            <div className="text-xs text-gray-400">剩餘股數</div>
                        </div>
                        <div className="text-center">
                            <div className="text-lg font-bold text-green-400">
                                {ipoStatus.initialPrice}
                            </div>
                            <div className="text-xs text-gray-400">每股價格</div>
                        </div>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <PermissionButton
                    requiredPermission={PERMISSIONS.MANAGE_MARKET}
                    token={token}
                    className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                    onClick={async () => {
                        try {
                            await openMarket(token);
                            showNotification('市場已開盤', 'success');
                            const status = await getAdminMarketStatus(token);
                            setMarketStatus(status);
                        } catch (error) {
                            showNotification(`開盤失敗: ${error.message}`, 'error');
                        }
                    }}
                    disabled={marketStatus?.is_open}
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
                            const status = await getAdminMarketStatus(token);
                            setMarketStatus(status);
                        } catch (error) {
                            showNotification(`收盤失敗: ${error.message}`, 'error');
                        }
                    }}
                    disabled={marketStatus && !marketStatus.is_open}
                >
                    手動收盤
                </PermissionButton>

                <PermissionButton
                    requiredPermission={PERMISSIONS.MANAGE_MARKET}
                    token={token}
                    className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600"
                    onClick={handleCallAuction}
                    disabled={callAuctionLoading}
                >
                    {callAuctionLoading ? "撮合中..." : "集合競價"}
                </PermissionButton>

                <PermissionButton
                    requiredPermission={PERMISSIONS.MANAGE_MARKET}
                    token={token}
                    className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                    onClick={() => setShowIpoModal(true)}
                >
                    更新 IPO 參數
                </PermissionButton>

                <PermissionButton
                    requiredPermission={PERMISSIONS.MANAGE_MARKET}
                    token={token}
                    className="bg-yellow-500 text-white px-4 py-2 rounded hover:bg-yellow-600"
                    onClick={handleIpoReset}
                >
                    重置 IPO
                </PermissionButton>

                <PermissionButton
                    requiredPermission={PERMISSIONS.MANAGE_MARKET}
                    token={token}
                    className="bg-indigo-500 text-white px-4 py-2 rounded hover:bg-indigo-600"
                    onClick={() => setShowTradingLimitModal(true)}
                >
                    設定漲跌限制
                </PermissionButton>
            </div>

            {/* IPO 更新 Modal */}
            {showIpoModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-[#1A325F] p-6 rounded-lg border border-[#294565] max-w-md w-full mx-4">
                        <h3 className="text-lg font-bold text-[#92cbf4] mb-4">更新 IPO 參數</h3>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-[#7BC2E6] mb-1">
                                    剩餘股數 (留空則不更新)
                                </label>
                                <input
                                    type="number"
                                    value={ipoForm.sharesRemaining}
                                    onChange={(e) => setIpoForm({...ipoForm, sharesRemaining: e.target.value})}
                                    placeholder="例如: 0"
                                    className="w-full px-3 py-2 bg-[#0f203e] border border-[#294565] rounded text-white"
                                />
                                {ipoStatus && (
                                    <p className="mt-1 text-xs text-gray-400">
                                        目前: {ipoStatus.sharesRemaining?.toLocaleString()} 股
                                    </p>
                                )}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-[#7BC2E6] mb-1">
                                    IPO 價格 (留空則不更新)
                                </label>
                                <input
                                    type="number"
                                    value={ipoForm.initialPrice}
                                    onChange={(e) => setIpoForm({...ipoForm, initialPrice: e.target.value})}
                                    placeholder="例如: 25"
                                    className="w-full px-3 py-2 bg-[#0f203e] border border-[#294565] rounded text-white"
                                />
                                {ipoStatus && (
                                    <p className="mt-1 text-xs text-gray-400">
                                        目前: {ipoStatus.initialPrice} 點/股
                                    </p>
                                )}
                            </div>
                            <div className="border border-blue-600 bg-blue-900/20 p-3 rounded-lg">
                                <p className="text-sm text-blue-200">
                                    💡 提示：設定剩餘股數為 0 可以強制市價單使用限價單撮合，實現價格發現機制
                                </p>
                            </div>
                            <div className="flex gap-3 mt-4">
                                <button
                                    onClick={() => setShowIpoModal(false)}
                                    className="flex-1 px-4 py-2 bg-[#294565] text-[#92cbf4] rounded hover:bg-[#1A325F]"
                                >
                                    取消
                                </button>
                                <button
                                    onClick={handleIpoUpdate}
                                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                                >
                                    更新
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* 設定漲跌限制 Modal */}
            {showTradingLimitModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-[#1A325F] p-6 rounded-lg border border-[#294565] max-w-md w-full mx-4">
                        <h3 className="text-lg font-bold text-[#92cbf4] mb-4">設定漲跌限制</h3>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-[#7BC2E6] mb-1">
                                    漲跌限制百分比
                                </label>
                                <div className="relative">
                                    <input
                                        type="number"
                                        min="0"
                                        step="10"
                                        value={tradingLimitPercent}
                                        onChange={(e) => {
                                            const value = e.target.value;
                                            if (value === "" || (!isNaN(value) && parseFloat(value) >= 0)) {
                                                setTradingLimitPercent(value);
                                            }
                                        }}
                                        placeholder="輸入百分比數字 (0-100)"
                                        className="w-full px-3 py-2 pr-8 bg-[#0f203e] border border-[#294565] rounded text-white"
                                    />
                                    <span className="absolute top-2 right-3 text-[#7BC2E6]">%</span>
                                </div>
                            </div>
                            <div className="flex gap-3 mt-4">
                                <button
                                    onClick={() => setShowTradingLimitModal(false)}
                                    className="flex-1 px-4 py-2 bg-[#294565] text-[#92cbf4] rounded hover:bg-[#1A325F]"
                                >
                                    取消
                                </button>
                                <button
                                    onClick={handleSetTradingLimit}
                                    className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                                >
                                    設定
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminDashboard;
