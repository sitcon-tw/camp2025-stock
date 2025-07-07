import {
    PERMISSIONS,
    usePermissionContext,
} from "@/contexts/PermissionContext";
import { useEffect, useState } from "react";
import { PermissionButton, PermissionGuard } from "./PermissionGuard";
import { RoleManagement } from "./RoleManagement";
// import { QuickRoleSetup } from "./QuickRoleSetup";
import {
    closeMarket,
    forceSettlement,
    getAdminMarketStatus,
    getIpoStatus,
    getUserAssets,
    givePoints,
    openMarket,
    resetAllData,
    resetIpo,
    setTradingLimit,
    updateIpo,
} from "@/lib/api";
import { AnnouncementManagement } from "./AnnouncementManagement";
import Modal from "./Modal";

/**
 * 管理員儀表板組件
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

    const [showPointsModal, setShowPointsModal] = useState(false);
    const [pointsForm, setPointsForm] = useState({
        username: "",
        amount: "",
    });

    // Auto-complete related state
    const [students, setStudents] = useState([]);
    const [suggestions, setSuggestions] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [studentsLoading, setStudentsLoading] = useState(false);

    // Fetch students data when component mounts
    useEffect(() => {
        if (token) {
            fetchStudents();
        }
    }, [token]);

    // Fetch students for auto-complete
    const fetchStudents = async () => {
        try {
            setStudentsLoading(true);
            const data = await getUserAssets(token);
            if (Array.isArray(data)) {
                setStudents(data);
            } else {
                console.error("學生資料格式錯誤:", data);
                setStudents([]);
            }
        } catch (error) {
            console.error("獲取學生列表錯誤:", error);
            setStudents([]);
        } finally {
            setStudentsLoading(false);
        }
    };

    // Handle username input change with auto-complete
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

        // Filter students based on input
        const filteredSuggestions = students
            .filter(
                (student) =>
                    student &&
                    typeof student.username === "string" &&
                    student.username
                        .toLowerCase()
                        .includes(value.toLowerCase()),
            )
            .map((student) => ({
                value: student.username,
                label: `${student.username}${student.team ? ` (${student.team})` : ""}`,
            }))
            .slice(0, 5); // Limit to 5 suggestions

        setSuggestions(filteredSuggestions);
        setShowSuggestions(filteredSuggestions.length > 0);
    };

    // Select a suggestion
    const selectSuggestion = (suggestion) => {
        setPointsForm({
            ...pointsForm,
            username: suggestion.value,
        });
        setShowSuggestions(false);
        setSuggestions([]);
    };

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

    // 發放點數
    const handleGivePoints = async () => {
        try {
            await givePoints(
                token,
                pointsForm.username,
                "user",
                parseInt(pointsForm.amount),
            );
            showNotification(
                `成功發放 ${pointsForm.amount} 點給 ${pointsForm.username}`,
                "success",
            );
            setShowPointsModal(false);
            setPointsForm({ username: "", amount: "" });
        } catch (error) {
            showNotification(
                `發放點數失敗: ${error.message}`,
                "error",
            );
        }
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
                    className={`rounded-lg border p-4 ${
                        notification.type === "success"
                            ? "border-green-500/30 bg-green-600/20 text-green-400"
                            : notification.type === "error"
                              ? "border-red-500/30 bg-red-600/20 text-red-400"
                              : "border-blue-500/30 bg-blue-600/20 text-blue-400"
                    }`}
                >
                    {notification.message}
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
                                    className={`flex items-center space-x-2 border-b-2 px-1 py-4 text-sm font-medium ${
                                        activeSection === section.id
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
                            setShowPointsModal={setShowPointsModal}
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

            {/* 發放點數模態框 */}
            <Modal
                isOpen={showPointsModal}
                onClose={() => {
                    setShowPointsModal(false);
                    setPointsForm({ username: "", amount: "" });
                    setShowSuggestions(false);
                    setSuggestions([]);
                }}
                title="發放點數"
                size="md"
            >
                <div className="space-y-4">
                    <div>
                        <label className="mb-1 block text-sm font-medium text-[#7BC2E6]">
                            使用者名稱
                        </label>
                        <div className="relative">
                            <input
                                type="text"
                                placeholder={
                                    studentsLoading
                                        ? "正在載入使用者資料..."
                                        : "搜尋學生姓名..."
                                }
                                value={pointsForm.username}
                                onChange={(e) =>
                                    handleUsernameChange(
                                        e.target.value,
                                    )
                                }
                                onFocus={() => {
                                    // 重新觸發搜尋以顯示建議
                                    if (
                                        pointsForm.username.trim() !==
                                        ""
                                    ) {
                                        handleUsernameChange(
                                            pointsForm.username,
                                        );
                                    }
                                }}
                                onBlur={() => {
                                    // 延遲隱藏建議，讓點選事件能夠觸發
                                    setTimeout(
                                        () =>
                                            setShowSuggestions(false),
                                        200,
                                    );
                                }}
                                disabled={studentsLoading}
                                className="w-full rounded border border-[#294565] bg-[#0f203e] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
                            />
                            {/* 自動完成建議 */}
                            {showSuggestions &&
                                suggestions.length > 0 && (
                                    <div className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md border border-[#294565] bg-[#0f203e] shadow-lg">
                                        {suggestions.map(
                                            (suggestion, index) => (
                                                <div
                                                    key={index}
                                                    onMouseDown={(
                                                        e,
                                                    ) => {
                                                        e.preventDefault(); // 防止blur事件影響點選
                                                        selectSuggestion(
                                                            suggestion,
                                                        );
                                                    }}
                                                    className="cursor-pointer border-b border-[#294565] px-3 py-2 text-sm text-white transition-colors last:border-b-0 hover:bg-[#1A325F]"
                                                >
                                                    <div className="flex items-center justify-between">
                                                        <span>
                                                            {
                                                                suggestion.label
                                                            }
                                                        </span>
                                                        <span className="text-xs text-gray-400">
                                                            個人
                                                        </span>
                                                    </div>
                                                </div>
                                            ),
                                        )}
                                    </div>
                                )}
                            {/* 載入提示 */}
                            {studentsLoading && (
                                <div className="absolute top-1/2 right-3 -translate-y-1/2">
                                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-[#7BC2E6] border-t-transparent"></div>
                                </div>
                            )}
                        </div>
                    </div>
                    <div>
                        <label className="mb-1 block text-sm font-medium text-[#7BC2E6]">
                            點數數量
                        </label>
                        <input
                            type="number"
                            placeholder="點數數量"
                            value={pointsForm.amount}
                            onChange={(e) =>
                                setPointsForm({
                                    ...pointsForm,
                                    amount: e.target.value,
                                })
                            }
                            className="w-full rounded border border-[#294565] bg-[#0f203e] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        />
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={() => {
                                setShowPointsModal(false);
                                setPointsForm({
                                    username: "",
                                    amount: "",
                                });
                                setShowSuggestions(false);
                                setSuggestions([]);
                            }}
                            className="flex-1 rounded bg-[#294565] px-4 py-2 text-[#92cbf4] hover:bg-[#1A325F]"
                        >
                            取消
                        </button>
                        <button
                            onClick={handleGivePoints}
                            disabled={
                                !pointsForm.username ||
                                !pointsForm.amount ||
                                studentsLoading
                            }
                            className="flex-1 rounded bg-green-600 px-4 py-2 text-white hover:bg-green-700 disabled:opacity-50"
                        >
                            發放
                        </button>
                    </div>
                </div>
            </Modal>

            {/* 發布公告模態框 */}
        </div>
    );
};

/**
 * 功能概覽區塊
 */
const OverviewSection = ({
    token,
    setShowPointsModal,
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

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {/* 角色管理卡片 */}
            <PermissionGuard
                requiredPermission={PERMISSIONS.MANAGE_USERS}
                token={token}
            >
                <div className="rounded-lg border border-blue-500/30 bg-blue-600/20 p-6">
                    <div className="mb-4 flex items-center">
                        <span className="mr-3 text-2xl">👥</span>
                        <h3 className="text-lg font-semibold text-blue-400">
                            角色管理
                        </h3>
                    </div>
                    <p className="mb-4 text-sm text-blue-300">
                        管理使用者角色和權限，將使用者從學員提升為管理員角色
                    </p>
                    <div className="text-xs text-blue-300">
                        • 查看所有使用者
                        <br />
                        • 變更使用者角色
                        <br />• 權限狀態檢視
                    </div>
                </div>
            </PermissionGuard>

            {/* 系統管理卡片 */}
            <PermissionGuard
                requiredPermission={PERMISSIONS.SYSTEM_ADMIN}
                token={token}
            >
                <div className="rounded-lg border border-red-500/30 bg-red-600/20 p-6">
                    <div className="mb-4 flex items-center">
                        <span className="mr-3 text-2xl">⚙️</span>
                        <h3 className="text-lg font-semibold text-red-400">
                            系統管理
                        </h3>
                    </div>
                    <p className="mb-4 text-sm text-red-300">
                        危險操作區域，包含系統重置和強制結算功能
                    </p>
                    <div className="text-xs text-red-300">
                        • 重置所有資料
                        <br />
                        • 強制結算
                        <br />• 系統設定
                    </div>
                </div>
            </PermissionGuard>

            {/* 點數管理卡片 */}
            <PermissionGuard
                requiredPermission={PERMISSIONS.GIVE_POINTS}
                token={token}
            >
                <div className="rounded-lg border border-green-500/30 bg-green-600/20 p-6">
                    <div className="mb-4 flex items-center">
                        <span className="mr-3 text-2xl">💰</span>
                        <h3 className="text-lg font-semibold text-green-400">
                            點數管理
                        </h3>
                    </div>
                    <p className="mb-4 text-sm text-green-300">
                        發放點數給使用者，查看點數交易記錄
                    </p>
                    <div className="text-xs text-green-300">
                        • 發放點數
                        <br />
                        • 查看記錄
                        <br />• 點數統計
                    </div>
                </div>
            </PermissionGuard>
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
                    onGivePoints={() => setShowPointsModal(true)}
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

            {/* 市場管理區塊 */}
            <PermissionGuard
                requiredPermission={PERMISSIONS.MANAGE_MARKET}
                token={token}
            >
                <MarketManagementSection
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

    return (
        <div className="rounded-lg border border-[#294565] bg-[#1A325F] p-6 shadow">
            <h2 className="mb-2 mb-4 text-center text-2xl font-bold text-red-400">
                點底下兩個按鈕前請三思哦哦哦
            </h2>
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
                                    <li>
                                        清除所有使用者的持股和點數資料
                                    </li>
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
                        {isProcessing ? "重置中..." : "確認重置"}
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
                            <span className="text-2xl">💰</span>
                            <div>
                                <h4 className="font-semibold text-orange-400">
                                    強制結算說明
                                </h4>
                                <p className="mt-1 text-sm text-orange-300">
                                    這個操作將會：
                                </p>
                                <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-orange-300">
                                    <li>立即執行所有未結算的交易</li>
                                    <li>強制撮合所有掛單</li>
                                    <li>更新所有使用者的資產狀態</li>
                                    <li>可能影響正在進行的交易</li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    <p className="text-[#7BC2E6]">
                        確定要執行強制結算嗎？這可能會影響正在進行的交易。
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
                        {isProcessing ? "結算中..." : "確認結算"}
                    </button>
                </div>
            </Modal>
        </div>
    );
};

/**
 * 用戶管理區塊
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
    onGivePoints,
    showNotification,
}) => (
    <div className="rounded-lg border border-[#294565] bg-[#1A325F] p-6 shadow">
        <h2 className="mb-4 text-xl font-bold text-green-400">
            點數管理
        </h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <PermissionButton
                requiredPermission={PERMISSIONS.GIVE_POINTS}
                token={token}
                className="rounded bg-green-500 px-4 py-2 text-white hover:bg-green-600"
                onClick={onGivePoints}
            >
                發放點數
            </PermissionButton>

            <PermissionButton
                requiredPermission={PERMISSIONS.GIVE_POINTS}
                token={token}
                className="rounded bg-yellow-500 px-4 py-2 text-white hover:bg-yellow-600"
                onClick={() =>
                    showNotification("點數記錄功能尚未實作", "info")
                }
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
    const [showTradingLimitModal, setShowTradingLimitModal] =
        useState(false);
    const [tradingLimitPercent, setTradingLimitPercent] =
        useState(10);
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
            <h2 className="mb-4 text-xl font-bold text-orange-400">
                市場管理
            </h2>

            {/* 市場狀態顯示 */}
            {marketStatus && (
                <div className="mb-6 rounded-lg border border-[#294565] bg-[#0f203e] p-4">
                    <div className="mb-2 flex items-center justify-between">
                        <span className="text-[#7BC2E6]">
                            市場狀態:
                        </span>
                        <span
                            className={`rounded-full px-3 py-1 text-sm font-medium ${
                                marketStatus.is_open
                                    ? "bg-green-600 text-green-100"
                                    : "bg-red-600 text-red-100"
                            }`}
                        >
                            {marketStatus.is_open
                                ? "開盤中"
                                : "已收盤"}
                        </span>
                    </div>
                    {marketStatus.last_updated && (
                        <div className="text-sm text-gray-400">
                            最後更新:{" "}
                            {new Date(
                                marketStatus.last_updated,
                            ).toLocaleString("zh-TW")}
                        </div>
                    )}
                </div>
            )}

            {/* IPO狀態顯示 */}
            {ipoStatus && (
                <div className="mb-6 rounded-lg border border-[#294565] bg-[#0f203e] p-4">
                    <h3 className="mb-2 text-lg font-medium text-[#7BC2E6]">
                        IPO 狀態
                    </h3>
                    <div className="mb-4 grid grid-cols-3 gap-4">
                        <div className="text-center">
                            <div className="text-lg font-bold text-white">
                                {ipoStatus.initialShares?.toLocaleString()}
                            </div>
                            <div className="text-xs text-gray-400">
                                初始股數
                            </div>
                        </div>
                        <div className="text-center">
                            <div className="text-lg font-bold text-orange-400">
                                {ipoStatus.sharesRemaining?.toLocaleString()}
                            </div>
                            <div className="text-xs text-gray-400">
                                剩餘股數
                            </div>
                        </div>
                        <div className="text-center">
                            <div className="text-lg font-bold text-green-400">
                                {ipoStatus.initialPrice}
                            </div>
                            <div className="text-xs text-gray-400">
                                每股價格
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                <PermissionButton
                    requiredPermission={PERMISSIONS.MANAGE_MARKET}
                    token={token}
                    className="rounded bg-green-500 px-4 py-2 text-white hover:bg-green-600"
                    onClick={async () => {
                        try {
                            await openMarket(token);
                            showNotification("市場已開盤", "success");
                            const status =
                                await getAdminMarketStatus(token);
                            setMarketStatus(status);
                        } catch (error) {
                            showNotification(
                                `開盤失敗: ${error.message}`,
                                "error",
                            );
                        }
                    }}
                    disabled={marketStatus?.is_open}
                >
                    手動開盤
                </PermissionButton>

                <PermissionButton
                    requiredPermission={PERMISSIONS.MANAGE_MARKET}
                    token={token}
                    className="rounded bg-red-500 px-4 py-2 text-white hover:bg-red-600"
                    onClick={async () => {
                        try {
                            await closeMarket(token);
                            showNotification("市場已收盤", "success");
                            const status =
                                await getAdminMarketStatus(token);
                            setMarketStatus(status);
                        } catch (error) {
                            showNotification(
                                `收盤失敗: ${error.message}`,
                                "error",
                            );
                        }
                    }}
                    disabled={marketStatus && !marketStatus.is_open}
                >
                    手動收盤
                </PermissionButton>

                <PermissionButton
                    requiredPermission={PERMISSIONS.MANAGE_MARKET}
                    token={token}
                    className="rounded bg-blue-500 px-4 py-2 text-white hover:bg-blue-600"
                    onClick={() => setShowIpoModal(true)}
                >
                    更新 IPO 參數
                </PermissionButton>

                <PermissionButton
                    requiredPermission={PERMISSIONS.MANAGE_MARKET}
                    token={token}
                    className="rounded bg-yellow-500 px-4 py-2 text-white hover:bg-yellow-600"
                    onClick={handleIpoReset}
                >
                    重置 IPO
                </PermissionButton>

                <PermissionButton
                    requiredPermission={PERMISSIONS.MANAGE_MARKET}
                    token={token}
                    className="rounded bg-indigo-500 px-4 py-2 text-white hover:bg-indigo-600"
                    onClick={() => setShowTradingLimitModal(true)}
                >
                    設定漲跌限制
                </PermissionButton>
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
                                目前:{" "}
                                {ipoStatus.sharesRemaining?.toLocaleString()}{" "}
                                股
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
                            💡 提示：設定剩餘股數為 0
                            可以強制市價單使用限價單撮合，實現價格發現機制
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

            {/* 設定漲跌限制 Modal */}
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
                                step="10"
                                value={tradingLimitPercent}
                                onChange={(e) => {
                                    const value = e.target.value;
                                    if (
                                        value === "" ||
                                        (!isNaN(value) &&
                                            parseFloat(value) >= 0)
                                    ) {
                                        setTradingLimitPercent(value);
                                    }
                                }}
                                placeholder="輸入百分比數字 (0-100)"
                                className="w-full rounded border border-[#294565] bg-[#0f203e] px-3 py-2 pr-8 text-white"
                            />
                            <span className="absolute top-2 right-3 text-[#7BC2E6]">
                                %
                            </span>
                        </div>
                    </div>
                    <div className="mt-4 flex gap-3">
                        <button
                            onClick={() =>
                                setShowTradingLimitModal(false)
                            }
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
        </div>
    );
};

export default AdminDashboard;
