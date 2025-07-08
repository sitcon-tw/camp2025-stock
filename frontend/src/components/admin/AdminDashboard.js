import {
    PERMISSIONS,
    usePermissionContext,
} from "@/contexts/PermissionContext";
import { useEffect, useState } from "react";
import { PermissionButton, PermissionGuard } from "./PermissionGuard";
import { RoleManagement } from "./RoleManagement";
// import { QuickRoleSetup } from "./QuickRoleSetup";
import {
    forceSettlement,
    getIpoStatus,
    getTeams,
    getUserAssets,
    givePoints,
    resetAllData,
    resetIpo,
    setTradingLimit,
    updateIpo,
} from "@/lib/api";
import { AnnouncementManagement } from "./AnnouncementManagement";
import { Modal } from "../ui";

/**
 * 管理員儀表板設定
 * 使用權限驅動的 UI 控制
 */
export const AdminDashboard = ({ token }) => {
    const { role, loading, isAdmin } = usePermissionContext();
    const [activeSection, setActiveSection] = useState("overview");
    const [notification, setNotification] = useState({
        show: false,
        message: "",
        type: "info",
    });

    // 顯示通知
    const showNotification = (message, type = "info") => {
        setNotification({ show: true, message, type });
        setTimeout(
            () =>
                setNotification({
                    show: false,
                    message: "",
                    type: "info",
                }),
            3000,
        );
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="text-lg text-gray-600">
                    載入權限中...
                </div>
            </div>
        );
    }

    // 如果沒有 role 且有 token，繼續顯示載入中（可能在 fallback 驗證中）
    if (!role && token) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="text-lg text-gray-600">
                    驗證權限中...
                </div>
            </div>
        );
    }

    // 檢查是否有管理權限（admin、point_manager、announcer 都可以訪問）
    const hasManagementAccess =
        isAdmin() || role === "point_manager" || role === "announcer";

    if (!hasManagementAccess) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="text-center">
                    <div className="mb-2 text-lg text-red-600">
                        權限不足：需要管理相關權限
                    </div>
                    <div className="text-sm text-gray-600">
                        您的角色：{role}
                    </div>
                    <div className="text-sm text-gray-600">
                        允許的角色：admin、point_manager、announcer
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* 通知提示 */}
            {notification.show && (
                <div
                    className={`fixed top-4 right-4 z-50 max-w-md rounded-lg border p-4 shadow-lg transition-all duration-300 ${notification.type === "success"
                            ? "border-green-500/30 bg-green-600/20 text-green-400"
                            : notification.type === "error"
                                ? "border-red-500/30 bg-red-600/20 text-red-400"
                                : "border-blue-500/30 bg-blue-600/20 text-blue-400"
                        }`}
                >
                    <div className="flex items-center space-x-2">
                        {notification.type === "success" && (
                            <svg className="h-5 w-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                        )}
                        {notification.type === "error" && (
                            <svg className="h-5 w-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        )}
                        {notification.type === "info" && (
                            <svg className="h-5 w-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        )}
                        <span className="break-words">{notification.message}</span>
                    </div>
                </div>
            )}

            {/* 功能導航 */}
            <div className="rounded-lg border border-[#294565] bg-[#1A325F] shadow">
                <div className="border-b border-[#294565]">
                    <nav className="flex space-x-8 px-6">
                        {[
                            {
                                id: "overview",
                                label: "功能概覽",
                            },
                            {
                                id: "roles",
                                label: "角色管理",
                                permission: PERMISSIONS.MANAGE_USERS,
                            },
                            {
                                id: "system",
                                label: "超級恐怖的地方",
                                permission: PERMISSIONS.SYSTEM_ADMIN,
                            },
                        ].map((section) => (
                            <PermissionGuard
                                key={section.id}
                                requiredPermission={
                                    section.permission
                                }
                                token={token}
                                fallback={
                                    section.id === "overview"
                                        ? null
                                        : undefined
                                }
                            >
                                <button
                                    onClick={() =>
                                        setActiveSection(section.id)
                                    }
                                    className={`flex items-center space-x-2 border-b-2 px-1 py-4 text-sm font-medium ${activeSection === section.id
                                            ? "border-[#469FD2] text-[#92cbf4]"
                                            : "border-transparent text-[#557797] hover:text-[#92cbf4]"
                                        }`}
                                >
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
                            showNotification={showNotification}
                        />
                    )}
                    {activeSection === "roles" && (
                        <PermissionGuard
                            requiredPermission={
                                PERMISSIONS.MANAGE_USERS
                            }
                            token={token}
                            fallback={
                                <div className="text-red-600">
                                    權限不足：需要用戶管理權限
                                </div>
                            }
                        >
                            <div className="space-y-6">
                                {/* <QuickRoleSetup token={token} /> */}
                                <RoleManagement token={token} />
                            </div>
                        </PermissionGuard>
                    )}
                    {activeSection === "system" && (
                        <PermissionGuard
                            requiredPermission={
                                PERMISSIONS.SYSTEM_ADMIN
                            }
                            token={token}
                            fallback={
                                <div className="text-red-600">
                                    權限不足：需要系統管理權限
                                </div>
                            }
                        >
                            <SystemManagementSection
                                token={token}
                                showNotification={showNotification}
                            />
                        </PermissionGuard>
                    )}
                </div>
            </div>


            {/* 發布公告模態框 */}
        </div>
    );
};

/**
 * 功能概覽區塊
 */
const OverviewSection = ({
    token,
    showNotification,
}) => (
    <div className="space-y-6">
        <div>
            <h2 className="mb-2 text-2xl font-bold text-[#92cbf4]">
                管理員功能概覽
            </h2>
            <p className="text-[#557797]">
                選擇上方頁簽來使用不同的管理功能
            </p>
        </div>


        {/* 其他管理功能 */}
        <div className="space-y-6">
            {/* 點數管理區塊 */}
            <PermissionGuard
                requiredPermission={PERMISSIONS.GIVE_POINTS}
                token={token}
            >
                <PointManagementSection
                    token={token}
                    showNotification={showNotification}
                />
            </PermissionGuard>

            {/* 公告管理區塊 */}
            <PermissionGuard
                requiredPermission={PERMISSIONS.CREATE_ANNOUNCEMENT}
                token={token}
            >
                <AnnouncementManagement token={token} />
            </PermissionGuard>

            {/* IPO 狀態區塊 */}
            <PermissionGuard
                requiredPermission={PERMISSIONS.MANAGE_MARKET}
                token={token}
            >
                <IpoStatusSection
                    token={token}
                    showNotification={showNotification}
                />
            </PermissionGuard>

        </div>
    </div>
);

/**
 * 系統管理區塊
 */
const SystemManagementSection = ({ token, showNotification }) => {
    const [showResetModal, setShowResetModal] = useState(false);
    const [showSettlementModal, setShowSettlementModal] =
        useState(false);
    const [isProcessing, setIsProcessing] = useState(false);

    // 市場管理相關狀態
    const [ipoStatus, setIpoStatus] = useState(null);
    const [showIpoModal, setShowIpoModal] = useState(false);
    const [showTradingLimitModal, setShowTradingLimitModal] =
        useState(false);
    const [tradingLimitPercent, setTradingLimitPercent] =
        useState(10);
    const [ipoForm, setIpoForm] = useState({
        sharesRemaining: "",
        initialPrice: "",
    });

    // 獲取IPO狀態
    useEffect(() => {
        const fetchIpoStatus = async () => {
            try {
                const status = await getIpoStatus(token);
                setIpoStatus(status);
            } catch (error) {
                console.error("獲取IPO狀態失敗:", error);
            }
        };

        fetchIpoStatus();
    }, [token]);

    const handleResetAllData = async () => {
        try {
            setIsProcessing(true);
            await resetAllData(token);
            showNotification("所有資料已成功重置", "success");
            setShowResetModal(false);
        } catch (error) {
            showNotification(`重置失敗: ${error.message}`, "error");
        } finally {
            setIsProcessing(false);
        }
    };

    const handleForceSettlement = async () => {
        try {
            setIsProcessing(true);
            await forceSettlement(token);
            showNotification("強制結算已完成", "success");
            setShowSettlementModal(false);
        } catch (error) {
            showNotification(
                `強制結算失敗: ${error.message}`,
                "error",
            );
        } finally {
            setIsProcessing(false);
        }
    };

    // 更新IPO
    const handleIpoUpdate = async () => {
        try {
            const sharesRemaining =
                ipoForm.sharesRemaining !== ""
                    ? parseInt(ipoForm.sharesRemaining)
                    : null;
            const initialPrice =
                ipoForm.initialPrice !== ""
                    ? parseInt(ipoForm.initialPrice)
                    : null;

            const result = await updateIpo(
                token,
                sharesRemaining,
                initialPrice,
            );

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
            showNotification(
                `IPO更新失敗: ${error.message}`,
                "error",
            );
        }
    };

    // 重置IPO
    const handleIpoReset = async () => {
        try {
            if (confirm("確定要重置IPO嗎？")) {
                const result = await resetIpo(token);
                showNotification(result.message, "success");

                // 重新取得IPO狀態
                const status = await getIpoStatus(token);
                setIpoStatus(status);
            }
        } catch (error) {
            showNotification(
                `IPO重置失敗: ${error.message}`,
                "error",
            );
        }
    };

    // 設定交易限制
    const handleSetTradingLimit = async () => {
        try {
            await setTradingLimit(
                token,
                parseFloat(tradingLimitPercent),
            );
            showNotification("交易限制設定成功！", "success");
            setShowTradingLimitModal(false);
        } catch (error) {
            showNotification(
                `設定交易限制失敗: ${error.message}`,
                "error",
            );
        }
    };

    return (
        <div className="rounded-lg border border-[#294565] bg-[#1A325F] p-6 shadow">
            {/* 危險操作區 */}
            <div className="border-t border-[#294565] pt-6">
                <h3 className="mb-2 text-center text-lg font-bold text-red-400">
                    ⚠️ 危險操作區域
                </h3>
                <p className="mb-4 text-center text-sm text-red-300">
                    點底下兩個按鈕前請三思哦哦哦
                </p>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <PermissionButton
                        requiredPermission={PERMISSIONS.SYSTEM_ADMIN}
                        token={token}
                        className="rounded bg-red-500 px-4 py-2 text-white hover:bg-red-600"
                        onClick={() => setShowResetModal(true)}
                    >
                        重置所有資料
                    </PermissionButton>

                    <PermissionButton
                        requiredPermission={PERMISSIONS.SYSTEM_ADMIN}
                        token={token}
                        className="rounded bg-orange-500 px-4 py-2 text-white hover:bg-orange-600"
                        onClick={() => setShowSettlementModal(true)}
                    >
                        全部學員股票結算
                    </PermissionButton>
                </div>
            </div>

            {/* IPO 更新 Modal */}
            <Modal
                isOpen={showIpoModal}
                onClose={() => setShowIpoModal(false)}
                title="更新 IPO 參數"
                size="md"
            >
                <div className="space-y-4">
                    <div>
                        <label className="mb-1 block text-sm font-medium text-[#7BC2E6]">
                            剩餘股數 (留空則不更新)
                        </label>
                        <input
                            type="number"
                            value={ipoForm.sharesRemaining}
                            onChange={(e) =>
                                setIpoForm({
                                    ...ipoForm,
                                    sharesRemaining: e.target.value,
                                })
                            }
                            placeholder="例如: 0"
                            className="w-full rounded border border-[#294565] bg-[#0f203e] px-3 py-2 text-white"
                        />
                        {ipoStatus && (
                            <p className="mt-1 text-xs text-gray-400">
                                目前: {ipoStatus.sharesRemaining?.toLocaleString()} 股
                            </p>
                        )}
                    </div>
                    <div>
                        <label className="mb-1 block text-sm font-medium text-[#7BC2E6]">
                            IPO 價格 (留空則不更新)
                        </label>
                        <input
                            type="number"
                            value={ipoForm.initialPrice}
                            onChange={(e) =>
                                setIpoForm({
                                    ...ipoForm,
                                    initialPrice: e.target.value,
                                })
                            }
                            placeholder="例如: 25"
                            className="w-full rounded border border-[#294565] bg-[#0f203e] px-3 py-2 text-white"
                        />
                        {ipoStatus && (
                            <p className="mt-1 text-xs text-gray-400">
                                目前: {ipoStatus.initialPrice} 點/股
                            </p>
                        )}
                    </div>
                    <div className="rounded-lg border border-blue-600 bg-blue-900/20 p-3">
                        <p className="text-sm text-blue-200">
                            💡 提示：設定剩餘股數為 0 可停止 IPO 發行
                        </p>
                    </div>
                    <div className="mt-4 flex gap-3">
                        <button
                            onClick={() => setShowIpoModal(false)}
                            className="flex-1 rounded bg-[#294565] px-4 py-2 text-[#92cbf4] hover:bg-[#1A325F]"
                        >
                            取消
                        </button>
                        <button
                            onClick={handleIpoUpdate}
                            className="flex-1 rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
                        >
                            更新
                        </button>
                    </div>
                </div>
            </Modal>

            {/* 交易限制設定 Modal */}
            <Modal
                isOpen={showTradingLimitModal}
                onClose={() => setShowTradingLimitModal(false)}
                title="設定漲跌限制"
                size="md"
            >
                <div className="space-y-4">
                    <div>
                        <label className="mb-1 block text-sm font-medium text-[#7BC2E6]">
                            漲跌限制百分比
                        </label>
                        <div className="relative">
                            <input
                                type="number"
                                min="0"
                                step="1"
                                value={tradingLimitPercent}
                                onChange={(e) => {
                                    const value = e.target.value;
                                    if (value === "" || (!isNaN(value) && parseFloat(value) >= 0)) {
                                        setTradingLimitPercent(value);
                                    }
                                }}
                                placeholder="輸入百分比數字 (0-100)"
                                className="w-full rounded border border-[#294565] bg-[#0f203e] px-3 py-2 pr-8 text-white"
                            />
                            <span className="absolute top-2 right-3 text-[#7BC2E6]">%</span>
                        </div>
                    </div>
                    <div className="mt-4 flex gap-3">
                        <button
                            onClick={() => setShowTradingLimitModal(false)}
                            className="flex-1 rounded bg-[#294565] px-4 py-2 text-[#92cbf4] hover:bg-[#1A325F]"
                        >
                            取消
                        </button>
                        <button
                            onClick={handleSetTradingLimit}
                            className="flex-1 rounded bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700"
                        >
                            設定
                        </button>
                    </div>
                </div>
            </Modal>

            {/* 重置所有資料確認模態框 */}
            <Modal
                isOpen={showResetModal}
                onClose={() => setShowResetModal(false)}
                title="確認重置所有資料？"
                size="md"
            >
                <div className="space-y-4">
                    <div className="rounded-lg border border-red-500/30 bg-red-600/10 p-4">
                        <div className="flex items-start space-x-3">
                            <span className="text-2xl">🚨</span>
                            <div>
                                <h4 className="font-semibold text-red-400">
                                    危險操作警告
                                </h4>
                                <p className="mt-1 text-sm text-red-300">
                                    這個操作將會：
                                </p>
                                <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-red-300">
                                    <li>清除所有使用者的持股和點數資料</li>
                                    <li>刪除所有交易記錄和訂單</li>
                                    <li>重置市場狀態和IPO設定</li>
                                    <li>清空所有公告和系統記錄</li>
                                </ul>
                                <p className="mt-3 font-medium text-red-400">
                                    ⚠️ 此操作無法撤銷！
                                </p>
                            </div>
                        </div>
                    </div>
                    <p className="text-[#7BC2E6]">
                        請確認您真的要重置所有系統資料嗎？
                    </p>
                </div>
                <div className="mt-6 flex justify-end space-x-3">
                    <button
                        onClick={() => setShowResetModal(false)}
                        disabled={isProcessing}
                        className="rounded bg-[#294565] px-4 py-2 text-[#92cbf4] hover:bg-[#1A325F] disabled:opacity-50"
                    >
                        取消
                    </button>
                    <button
                        onClick={handleResetAllData}
                        disabled={isProcessing}
                        className="rounded bg-red-600 px-4 py-2 text-white hover:bg-red-700 disabled:opacity-50"
                    >
                        {isProcessing ? "處理中..." : "確認重置"}
                    </button>
                </div>
            </Modal>

            {/* 強制結算確認模態框 */}
            <Modal
                isOpen={showSettlementModal}
                onClose={() => setShowSettlementModal(false)}
                title="確認強制結算？"
                size="md"
            >
                <div className="space-y-4">
                    <div className="rounded-lg border border-orange-500/30 bg-orange-600/10 p-4">
                        <div className="flex items-start space-x-3">
                            <span className="text-2xl">⚠️</span>
                            <div>
                                <h4 className="font-semibold text-orange-400">
                                    強制結算警告
                                </h4>
                                <p className="mt-1 text-sm text-orange-300">
                                    這個操作將會：
                                </p>
                                <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-orange-300">
                                    <li>將所有學員的股票按固定價格轉換為點數</li>
                                    <li>清除所有學員的持股</li>
                                    <li>取消所有進行中的掛單</li>
                                </ul>
                                <p className="mt-3 font-medium text-orange-400">
                                    ⚠️ 此操作無法撤銷！
                                </p>
                            </div>
                        </div>
                    </div>
                    <p className="text-[#7BC2E6]">
                        請確認您真的要執行強制結算嗎？
                    </p>
                </div>
                <div className="mt-6 flex justify-end space-x-3">
                    <button
                        onClick={() => setShowSettlementModal(false)}
                        disabled={isProcessing}
                        className="rounded bg-[#294565] px-4 py-2 text-[#92cbf4] hover:bg-[#1A325F] disabled:opacity-50"
                    >
                        取消
                    </button>
                    <button
                        onClick={handleForceSettlement}
                        disabled={isProcessing}
                        className="rounded bg-orange-600 px-4 py-2 text-white hover:bg-orange-700 disabled:opacity-50"
                    >
                        {isProcessing ? "處理中..." : "確認結算"}
                    </button>
                </div>
            </Modal>
        </div>
    );
};

/**
 * 用戶管理區塊 (暫時未使用)
 */
const UserManagementSection = ({ token }) => (
    <div className="rounded-lg bg-white p-6 shadow">
        <h2 className="mb-4 text-xl font-bold text-blue-600">
            用戶管理
        </h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <PermissionButton
                requiredPermission={PERMISSIONS.VIEW_ALL_USERS}
                token={token}
                className="rounded bg-blue-500 px-4 py-2 text-white hover:bg-blue-600"
                onClick={() => console.log("查看所有用戶")}
            >
                查看所有用戶
            </PermissionButton>

            <PermissionButton
                requiredPermission={PERMISSIONS.MANAGE_USERS}
                token={token}
                className="rounded bg-green-500 px-4 py-2 text-white hover:bg-green-600"
                onClick={() => console.log("管理用戶角色")}
            >
                管理用戶角色
            </PermissionButton>

            <PermissionButton
                requiredPermission={PERMISSIONS.VIEW_ALL_USERS}
                token={token}
                className="rounded bg-purple-500 px-4 py-2 text-white hover:bg-purple-600"
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
const PointManagementSection = ({
    token,
    showNotification,
}) => {
    const [pointsForm, setPointsForm] = useState({
        type: "user", // 'user', 'group', 'all_users', 'all_groups', 'multi_users', 'multi_groups'
        username: "",
        amount: "",
        multiTargets: [], // 多選目標列表
    });
    const [pointsLoading, setPointsLoading] = useState(false);
    const [students, setStudents] = useState([]);
    const [teams, setTeams] = useState([]);
    const [suggestions, setSuggestions] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [studentsLoading, setStudentsLoading] = useState(false);

    // 獲取學生和隊伍資料
    useEffect(() => {
        if (token) {
            fetchStudentsAndTeams();
        }
    }, [token]);

    const fetchStudentsAndTeams = async () => {
        try {
            setStudentsLoading(true);

            // 獲取學生資料
            const studentsData = await getUserAssets(token);
            if (Array.isArray(studentsData)) {
                setStudents(studentsData);
            } else {
                setStudents([]);
            }

            // 嘗試獲取隊伍資料
            try {
                const teamsData = await getTeams(token);
                if (Array.isArray(teamsData)) {
                    setTeams(teamsData);
                } else {
                    setTeams([]);
                }
            } catch (teamsError) {
                console.warn("獲取隊伍資料失敗:", teamsError);
                setTeams([]);
            }
        } catch (error) {
            console.error("獲取學生資料失敗:", error);
            setStudents([]);
            setTeams([]);
        } finally {
            setStudentsLoading(false);
        }
    };

    // 處理使用者名稱輸入變化
    const handleUsernameChange = (value) => {
        setPointsForm({
            ...pointsForm,
            username: value,
        });

        if (value.trim() === "" || studentsLoading) {
            setSuggestions([]);
            setShowSuggestions(false);
            return;
        }

        // 根據模式篩選建議
        const targetList = pointsForm.type === "user" || pointsForm.type === "multi_users" ? students : teams;
        const filteredSuggestions = targetList
            .filter((item) => {
                const searchTerm = pointsForm.type === "user" || pointsForm.type === "multi_users"
                    ? item.username
                    : item.name;
                return searchTerm && searchTerm.toLowerCase().includes(value.toLowerCase());
            })
            .map((item) => ({
                value: pointsForm.type === "user" || pointsForm.type === "multi_users"
                    ? item.username
                    : item.name,
                label: pointsForm.type === "user" || pointsForm.type === "multi_users"
                    ? `${item.username}${item.team ? ` (${item.team})` : ""}`
                    : `${item.name}${item.member_count ? ` (${item.member_count}人)` : ""}`,
                type: pointsForm.type === "user" || pointsForm.type === "multi_users" ? "user" : "group",
            }));

        setSuggestions(filteredSuggestions);
        setShowSuggestions(filteredSuggestions.length > 0);
    };

    // 選擇建議項目
    const selectSuggestion = (suggestion) => {
        setPointsForm({
            ...pointsForm,
            username: suggestion.value,
        });
        setShowSuggestions(false);
        setSuggestions([]);
    };

    // 添加多選目標
    const addMultiTarget = (suggestion) => {
        if (!pointsForm.multiTargets.some(target => target.value === suggestion.value)) {
            setPointsForm({
                ...pointsForm,
                multiTargets: [...pointsForm.multiTargets, suggestion],
                username: "",
            });
        }
        setShowSuggestions(false);
        setSuggestions([]);
    };

    // 移除多選目標
    const removeMultiTarget = (value) => {
        setPointsForm({
            ...pointsForm,
            multiTargets: pointsForm.multiTargets.filter(target => target.value !== value),
        });
    };

    // 處理點數發放
    const handleGivePoints = async () => {
        setPointsLoading(true);
        try {
            const amount = parseInt(pointsForm.amount);

            if (pointsForm.type === "all_users") {
                // 發放給全部使用者
                const promises = students.map((student) =>
                    givePoints(token, student.username, "user", amount)
                );
                await Promise.all(promises);
                showNotification(
                    `成功發放 ${amount} 點給 ${students.length} 位使用者！`,
                    "success"
                );
            } else if (pointsForm.type === "all_groups") {
                // 發放給全部團隊
                const promises = teams.map((team) =>
                    givePoints(token, team.name, "group", amount)
                );
                await Promise.all(promises);
                showNotification(
                    `成功發放 ${amount} 點給 ${teams.length} 個團隊！`,
                    "success"
                );
            } else if (
                pointsForm.type === "multi_users" ||
                pointsForm.type === "multi_groups"
            ) {
                // 多選模式
                const targetType = pointsForm.type === "multi_users" ? "user" : "group";
                const promises = pointsForm.multiTargets.map((target) =>
                    givePoints(token, target.value, targetType, amount)
                );
                await Promise.all(promises);
                showNotification(
                    `成功發放 ${amount} 點給 ${pointsForm.multiTargets.length} 個目標！`,
                    "success"
                );
            } else {
                // 單一目標模式
                await givePoints(token, pointsForm.username, pointsForm.type, amount);
                showNotification("點數發放成功！", "success");
            }

            // 重置表單
            setPointsForm({
                type: pointsForm.type,
                username: "",
                amount: "",
                multiTargets: [],
            });
            setSuggestions([]);
            setShowSuggestions(false);
        } catch (error) {
            showNotification(`發放點數失敗: ${error.message}`, "error");
        }
        setPointsLoading(false);
    };

    return (
        <div className="rounded-lg border border-[#294565] bg-[#1A325F] p-6 shadow">
            <h2 className="mb-4 text-xl font-bold text-green-400">
                點數管理
            </h2>
            <div className="space-y-4">
                {/* 發放模式選擇 */}
                <div className="space-y-4">
                    <label className="block text-sm font-medium text-[#7BC2E6]">
                        發放模式
                    </label>

                    {/* 個人/團隊切換 */}
                    <div className="flex items-center space-x-4">
                        <span className="text-[#7BC2E6]">個人</span>
                        <label className="relative inline-flex cursor-pointer items-center">
                            <input
                                type="checkbox"
                                checked={pointsForm.type === "group" || pointsForm.type === "multi_groups"}
                                onChange={(e) => {
                                    const isMulti = pointsForm.type.startsWith("multi_");
                                    let newType;

                                    if (isMulti) {
                                        newType = e.target.checked ? "multi_groups" : "multi_users";
                                    } else {
                                        newType = e.target.checked ? "group" : "user";
                                    }

                                    setPointsForm({
                                        ...pointsForm,
                                        type: newType,
                                        username: "",
                                        multiTargets: [],
                                    });
                                    setShowSuggestions(false);
                                    setSuggestions([]);
                                }}
                                className="peer sr-only"
                            />
                            <div className="peer h-6 w-11 rounded-full border border-gray-600 bg-[#0f203e] peer-checked:bg-[#7BC2E6] peer-focus:outline-none after:absolute after:top-[2px] after:left-[2px] after:h-5 after:w-5 after:rounded-full after:bg-white after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white"></div>
                        </label>
                        <span className="text-[#7BC2E6]">團隊</span>
                    </div>

                    {/* 多選開關 */}
                    <div className="flex items-center space-x-4">
                        <span className="text-[#7BC2E6]">單選</span>
                        <label className="relative inline-flex cursor-pointer items-center">
                            <input
                                type="checkbox"
                                checked={pointsForm.type.startsWith("multi_")}
                                onChange={(e) => {
                                    const isGroup = pointsForm.type === "group" || pointsForm.type === "multi_groups";
                                    const newType = e.target.checked
                                        ? isGroup ? "multi_groups" : "multi_users"
                                        : isGroup ? "group" : "user";

                                    setPointsForm({
                                        ...pointsForm,
                                        type: newType,
                                        username: "",
                                        multiTargets: [],
                                    });
                                    setShowSuggestions(false);
                                    setSuggestions([]);
                                }}
                                className="peer sr-only"
                            />
                            <div className="peer h-6 w-11 rounded-full border border-gray-600 bg-[#0f203e] peer-checked:bg-[#7BC2E6] peer-focus:outline-none after:absolute after:top-[2px] after:left-[2px] after:h-5 after:w-5 after:rounded-full after:bg-white after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white"></div>
                        </label>
                        <span className="text-[#7BC2E6]">多選</span>
                    </div>

                    {/* 全選按鈕 - 只在多選模式下顯示 */}
                    {pointsForm.type.startsWith("multi_") && (
                        <div className="grid grid-cols-2 gap-2">
                            <button
                                type="button"
                                onClick={() => {
                                    const targetList = pointsForm.type === "multi_users" ? students : teams;
                                    const allTargets = targetList.map((item) => ({
                                        value: pointsForm.type === "multi_users" ? item.username : item.name,
                                        label: pointsForm.type === "multi_users"
                                            ? `${item.username}${item.team ? ` (${item.team})` : ""}`
                                            : `${item.name}${item.member_count ? ` (${item.member_count}人)` : ""}`,
                                        type: pointsForm.type === "multi_users" ? "user" : "group",
                                    }));

                                    setPointsForm({
                                        ...pointsForm,
                                        multiTargets: allTargets,
                                        username: "",
                                    });
                                    setShowSuggestions(false);
                                    setSuggestions([]);
                                }}
                                className="rounded-lg bg-[#7BC2E6] px-4 py-2 text-sm text-black transition-colors hover:bg-[#6bb0d4]"
                            >
                                全選 {pointsForm.type === "multi_users"
                                    ? `所有個人 (${students.length})`
                                    : `所有團隊 (${teams.length})`}
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    setPointsForm({
                                        ...pointsForm,
                                        multiTargets: [],
                                        username: "",
                                    });
                                    setShowSuggestions(false);
                                    setSuggestions([]);
                                }}
                                disabled={pointsForm.multiTargets.length === 0}
                                className="rounded-lg bg-red-700/80 px-4 py-2 text-sm text-white transition-colors hover:bg-red-700/70 disabled:cursor-not-allowed disabled:bg-gray-600"
                            >
                                全部移除 ({pointsForm.multiTargets.length})
                            </button>
                        </div>
                    )}
                </div>

                {/* 條件顯示搜尋框 */}
                {(pointsForm.type.startsWith("multi_") || ["user", "group"].includes(pointsForm.type)) && (
                    <div className="relative">
                        <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                            {pointsForm.type.startsWith("multi_") ? "新增目標（搜尋選擇）" : "給誰（搜尋選擇）"}
                        </label>
                        <input
                            type="text"
                            value={pointsForm.username}
                            onChange={(e) => handleUsernameChange(e.target.value)}
                            onFocus={() => {
                                if (pointsForm.username.trim() !== "") {
                                    handleUsernameChange(pointsForm.username);
                                }
                            }}
                            onBlur={() => {
                                setTimeout(() => setShowSuggestions(false), 200);
                            }}
                            disabled={studentsLoading}
                            className="w-full rounded-xl border border-[#469FD2] bg-[#1A325F] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none disabled:cursor-not-allowed disabled:bg-[#0f203e] disabled:opacity-50"
                            placeholder={
                                studentsLoading ? "正在載入使用者資料..."
                                    : pointsForm.type === "user" || pointsForm.type === "multi_users"
                                        ? "搜尋學生姓名..."
                                        : "搜尋團隊名稱..."
                            }
                        />

                        {/* 搜尋建議下拉 */}
                        {showSuggestions && suggestions.length > 0 && (
                            <div className="absolute z-10 mt-1 max-h-48 w-full overflow-y-auto rounded-xl border border-[#469FD2] bg-[#0f203e] shadow-lg">
                                {suggestions.map((suggestion, index) => (
                                    <div
                                        key={index}
                                        onMouseDown={(e) => {
                                            e.preventDefault();
                                            if (pointsForm.type.startsWith("multi_")) {
                                                addMultiTarget(suggestion);
                                            } else {
                                                selectSuggestion(suggestion);
                                            }
                                        }}
                                        className="cursor-pointer border-b border-[#469FD2] px-3 py-2 text-sm text-white transition-colors last:border-b-0 hover:bg-[#1A325F]"
                                    >
                                        <div className="flex items-center justify-between">
                                            <span>{suggestion.label}</span>
                                            <span className="text-xs text-gray-400">
                                                {suggestion.type === "user" ? "個人" : "團隊"}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* 多選模式的已選目標列表 */}
                {pointsForm.type.startsWith("multi_") && pointsForm.multiTargets.length > 0 && (
                    <div>
                        <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                            已選擇的目標 ({pointsForm.multiTargets.length})
                        </label>
                        <div className="max-h-32 space-y-2 overflow-y-auto">
                            {pointsForm.multiTargets.map((target, index) => (
                                <div
                                    key={index}
                                    className="flex items-center justify-between rounded-lg bg-[#0f203e] px-3 py-2"
                                >
                                    <span className="text-sm text-white">{target.label}</span>
                                    <button
                                        type="button"
                                        onClick={() => removeMultiTarget(target.value)}
                                        className="text-sm text-red-400 hover:text-red-300"
                                    >
                                        移除
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* 全部模式的說明 */}
                {["all_users", "all_groups"].includes(pointsForm.type) && (
                    <div className="rounded-lg border border-[#469FD2] bg-[#0f203e] p-3">
                        <p className="text-sm text-[#7BC2E6]">
                            {pointsForm.type === "all_users"
                                ? `將發放給所有 ${students.length} 位使用者`
                                : `將發放給所有 ${teams.length} 個團隊`}
                        </p>
                    </div>
                )}

                {/* 點數數量輸入 */}
                <div>
                    <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                        給多少
                    </label>
                    <input
                        type="number"
                        value={pointsForm.amount}
                        onChange={(e) => setPointsForm({
                            ...pointsForm,
                            amount: e.target.value,
                        })}
                        className="w-full rounded-xl border border-[#469FD2] bg-[#1A325F] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        placeholder="輸入點數數量"
                    />
                </div>

                {/* 發放按鈕 */}
                <div className="flex w-full items-center justify-center">
                    <PermissionButton
                        requiredPermission={PERMISSIONS.GIVE_POINTS}
                        token={token}
                        onClick={handleGivePoints}
                        disabled={
                            pointsLoading ||
                            !pointsForm.amount ||
                            (["user", "group"].includes(pointsForm.type) && !pointsForm.username) ||
                            (pointsForm.type.startsWith("multi_") && pointsForm.multiTargets.length === 0)
                        }
                        className="w-full rounded-xl bg-green-600 px-6 py-3 text-white transition-colors hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-gray-600"
                    >
                        {pointsLoading ? "發放中..." : "發放點數"}
                    </PermissionButton>
                </div>

            </div>
        </div>
    );
};

/**
 * IPO 狀態區塊
 */
const IpoStatusSection = ({ token, showNotification }) => {
    const [ipoStatus, setIpoStatus] = useState(null);
    const [loading, setLoading] = useState(true);

    // 獲取 IPO 狀態
    useEffect(() => {
        const fetchIpoStatus = async () => {
            try {
                setLoading(true);
                const status = await getIpoStatus(token);
                setIpoStatus(status);
            } catch (error) {
                console.error("獲取IPO狀態失敗:", error);
                showNotification(`獲取IPO狀態失敗: ${error.message}`, "error");
            } finally {
                setLoading(false);
            }
        };

        if (token) {
            fetchIpoStatus();
        }
    }, [token, showNotification]);

    if (loading) {
        return (
            <div className="rounded-lg border border-[#294565] bg-[#1A325F] p-6 shadow">
                <h2 className="mb-4 text-xl font-bold text-purple-400">
                    IPO 狀態
                </h2>
                <div className="flex items-center justify-center py-8">
                    <div className="h-8 w-8 animate-spin rounded-full border-4 border-[#92cbf4] border-t-transparent"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="rounded-lg border border-[#294565] bg-[#1A325F] p-6 shadow">
            <h2 className="mb-4 text-xl font-bold text-purple-400">
                IPO 狀態
            </h2>

            {ipoStatus ? (
                <div className="space-y-4">
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {/* 剩餘股數 */}
                        <div className="rounded-lg border border-[#294565] bg-[#0f203e] p-4">
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-[#7BC2E6]">剩餘股數</span>
                                <span className="text-lg font-semibold text-white">
                                    {ipoStatus.sharesRemaining?.toLocaleString() || 'N/A'}
                                </span>
                            </div>
                        </div>

                        {/* IPO 價格 */}
                        <div className="rounded-lg border border-[#294565] bg-[#0f203e] p-4">
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-[#7BC2E6]">IPO 價格</span>
                                <span className="text-lg font-semibold text-white">
                                    {ipoStatus.initialPrice || 'N/A'} 點/股
                                </span>
                            </div>
                        </div>

                        {/* IPO 狀態 */}
                        <div className="rounded-lg border border-[#294565] bg-[#0f203e] p-4">
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-[#7BC2E6]">IPO 狀態</span>
                                <span className={`rounded-full px-3 py-1 text-sm font-medium ${ipoStatus.sharesRemaining > 0
                                        ? "bg-green-600 text-green-100"
                                        : "bg-red-600 text-red-100"
                                    }`}>
                                    {ipoStatus.sharesRemaining > 0 ? "進行中" : "已結束"}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* 詳細資訊 */}
                    <div className="rounded-lg border border-[#294565] bg-[#0f203e] p-4">
                        <h3 className="mb-3 text-lg font-semibold text-[#7BC2E6]">詳細資訊</h3>
                        <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                                <span className="text-gray-400">初始總股數:</span>
                                <span className="text-white">
                                    {ipoStatus.initialShares?.toLocaleString() || 'N/A'}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-400">已售出股數:</span>
                                <span className="text-white">
                                    {ipoStatus.initialShares && ipoStatus.sharesRemaining
                                        ? (ipoStatus.initialShares - ipoStatus.sharesRemaining).toLocaleString()
                                        : 'N/A'
                                    }
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-400">完成度:</span>
                                <span className="text-white">
                                    {ipoStatus.initialShares && ipoStatus.sharesRemaining
                                        ? `${((ipoStatus.initialShares - ipoStatus.sharesRemaining) / ipoStatus.initialShares * 100).toFixed(1)}%`
                                        : 'N/A'
                                    }
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="text-center py-8">
                    <p className="text-gray-400">無法獲取 IPO 狀態資訊</p>
                </div>
            )}
        </div>
    );
};

export default AdminDashboard;
