import { PERMISSIONS } from "@/contexts/PermissionContext";
import {
    getIpoDefaults,
    getTradingHours,
    getTransferFeeConfig,
    setTradingLimit,
    updateIpoDefaults,
    updateMarketTimes,
    updateTransferFeeConfig,
} from "@/lib/api";
import { useEffect, useState } from "react";
import { PermissionButton, PermissionGuard } from "./PermissionGuard";

/**
 * 系統設定管理組件
 * 統一管理所有可動態調整的系統參數
 */
export const SystemConfig = ({ token }) => {
    const [notification, setNotification] = useState({
        show: false,
        message: "",
        type: "info",
    });
    const [loading, setLoading] = useState(true);

    // 設定數據
    const [transferFeeConfig, setTransferFeeConfig] = useState(null);
    const [tradingHours, setTradingHours] = useState(null);
    const [ipoDefaults, setIpoDefaults] = useState(null);

    // 表單狀態
    const [feeForm, setFeeForm] = useState({
        feeRate: "",
        minFee: "",
    });
    const [tradingLimitForm, setTradingLimitForm] = useState({
        limitPercent: "",
    });
    const [ipoDefaultsForm, setIpoDefaultsForm] = useState({
        initialShares: "",
        initialPrice: "",
    });
    const [marketTimesForm, setMarketTimesForm] = useState({
        openTime: [],
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
            4000,
        );
    };

    // 載入所有設定
    const loadConfigs = async () => {
        try {
            setLoading(true);

            // 並行載入所有設定
            const [feeConfig, hours, defaults] =
                await Promise.allSettled([
                    getTransferFeeConfig(token),
                    getTradingHours(),
                    getIpoDefaults(token),
                ]);

            if (feeConfig.status === "fulfilled") {
                setTransferFeeConfig(feeConfig.value);
                setFeeForm({
                    feeRate: feeConfig.value.fee_rate || "",
                    minFee: feeConfig.value.min_fee || "",
                });
            }

            if (hours.status === "fulfilled") {
                setTradingHours(hours.value);
                setMarketTimesForm({
                    openTime: hours.value.openTime || [],
                });
            }

            if (defaults.status === "fulfilled") {
                setIpoDefaults(defaults.value);
                setIpoDefaultsForm({
                    initialShares:
                        defaults.value.default_initial_shares || "",
                    initialPrice:
                        defaults.value.default_initial_price || "",
                });
            }
        } catch (error) {
            console.error("載入設定失敗:", error);
            showNotification("載入設定失敗", "error");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (token) {
            loadConfigs();
        }
    }, [token]);

    // 更新轉帳手續費
    const handleUpdateTransferFee = async () => {
        try {
            if (!feeForm.feeRate || !feeForm.minFee) {
                showNotification("請填寫完整的手續費資訊", "error");
                return;
            }

            await updateTransferFeeConfig(
                token,
                parseFloat(feeForm.feeRate),
                parseInt(feeForm.minFee),
            );

            showNotification("轉帳手續費更新成功！", "success");
            await loadConfigs(); // 重新載入設定
        } catch (error) {
            showNotification(
                `更新轉帳手續費失敗: ${error.message}`,
                "error",
            );
        }
    };

    // 更新交易限制
    const handleUpdateTradingLimit = async () => {
        try {
            if (!tradingLimitForm.limitPercent) {
                showNotification("請填寫交易限制百分比", "error");
                return;
            }

            await setTradingLimit(
                token,
                parseFloat(tradingLimitForm.limitPercent),
            );
            showNotification("交易限制更新成功！", "success");
            setTradingLimitForm({ limitPercent: "" });
        } catch (error) {
            showNotification(
                `更新交易限制失敗: ${error.message}`,
                "error",
            );
        }
    };

    // 更新IPO預設值
    const handleUpdateIpoDefaults = async () => {
        try {
            if (
                !ipoDefaultsForm.initialShares ||
                !ipoDefaultsForm.initialPrice
            ) {
                showNotification("請填寫完整的IPO預設值", "error");
                return;
            }

            await updateIpoDefaults(
                token,
                parseInt(ipoDefaultsForm.initialShares),
                parseInt(ipoDefaultsForm.initialPrice),
            );

            showNotification("IPO預設值更新成功！", "success");
            await loadConfigs(); // 重新載入設定
        } catch (error) {
            showNotification(
                `更新IPO預設值失敗: ${error.message}`,
                "error",
            );
        }
    };

    // 新增交易時段
    const addTradingSession = () => {
        setMarketTimesForm((prev) => ({
            openTime: [...prev.openTime, { start: "", end: "" }],
        }));
    };

    // 移除交易時段
    const removeTradingSession = (index) => {
        setMarketTimesForm((prev) => ({
            openTime: prev.openTime.filter((_, i) => i !== index),
        }));
    };

    // 更新交易時段
    const updateTradingSession = (index, field, value) => {
        setMarketTimesForm((prev) => ({
            openTime: prev.openTime.map((session, i) =>
                i === index
                    ? { ...session, [field]: value }
                    : session,
            ),
        }));
    };

    // 儲存交易時間
    const handleUpdateTradingHours = async () => {
        try {
            // 驗證時間格式
            const validSessions = marketTimesForm.openTime.filter(
                (session) => session.start && session.end,
            );

            if (validSessions.length === 0) {
                showNotification("請至少設定一個交易時段", "error");
                return;
            }

            await updateMarketTimes(token, validSessions);
            showNotification("交易時間更新成功！", "success");
            await loadConfigs(); // 重新載入設定
        } catch (error) {
            showNotification(
                `更新交易時間失敗: ${error.message}`,
                "error",
            );
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="text-center">
                    <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-[#92cbf4] border-t-transparent"></div>
                    <p className="text-[#92cbf4]">
                        載入系統設定中...
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            {/* 通知區域 */}
            {notification.show && (
                <div
                    className={`rounded-lg border p-4 ${
                        notification.type === "success"
                            ? "border-green-500/30 bg-green-600/20 text-green-300"
                            : notification.type === "error"
                              ? "border-red-500/30 bg-red-600/20 text-red-300"
                              : "border-blue-500/30 bg-blue-600/20 text-blue-300"
                    }`}
                >
                    {notification.message}
                </div>
            )}

            <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
                {/* 轉帳手續費設定 */}
                <PermissionGuard
                    requiredPermission={PERMISSIONS.SYSTEM_ADMIN}
                    token={token}
                >
                    <div className="rounded-lg border border-[#294565] bg-[#1A325F] p-6 shadow">
                        <h3 className="mb-4 text-xl font-bold text-orange-400">
                            轉帳手續費設定
                        </h3>

                        {transferFeeConfig && (
                            <div className="mb-4 rounded border border-[#294565] bg-[#0f203e] p-3">
                                <div className="flex gap-6 text-white">
                                    <div className="flex flex-col items-start">
                                        <span className="mb-1 text-xs text-[#7BC2E6]">
                                            手續費率
                                        </span>
                                        <span className="font-semibold">
                                            {
                                                transferFeeConfig.feeRate
                                            }
                                            %
                                        </span>
                                    </div>
                                    <div className="flex flex-col items-start">
                                        <span className="mb-1 text-xs text-[#7BC2E6]">
                                            最低費用
                                        </span>
                                        <span className="font-semibold">
                                            {transferFeeConfig.minFee}{" "}
                                            點
                                        </span>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="space-y-4">
                            <div>
                                <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                    手續費率 (%)
                                </label>
                                <input
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    max="100"
                                    value={feeForm.feeRate}
                                    onChange={(e) =>
                                        setFeeForm((prev) => ({
                                            ...prev,
                                            feeRate: e.target.value,
                                        }))
                                    }
                                    className="w-full rounded border border-[#294565] bg-[#0f203e] p-3 text-white focus:border-[#469FD2] focus:outline-none"
                                    placeholder="例: 1.5"
                                />
                            </div>
                            <div>
                                <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                    最低手續費 (點)
                                </label>
                                <input
                                    type="number"
                                    min="1"
                                    value={feeForm.minFee}
                                    onChange={(e) =>
                                        setFeeForm((prev) => ({
                                            ...prev,
                                            minFee: e.target.value,
                                        }))
                                    }
                                    className="w-full rounded border border-[#294565] bg-[#0f203e] p-3 text-white focus:border-[#469FD2] focus:outline-none"
                                    placeholder="例: 5"
                                />
                            </div>
                            <PermissionButton
                                requiredPermission={
                                    PERMISSIONS.SYSTEM_ADMIN
                                }
                                token={token}
                                onClick={handleUpdateTransferFee}
                                className="w-full rounded bg-orange-500 px-4 py-2 text-white hover:bg-orange-600"
                            >
                                更新轉帳手續費
                            </PermissionButton>
                        </div>
                    </div>
                </PermissionGuard>

                {/* 交易限制設定 */}
                <PermissionGuard
                    requiredPermission={PERMISSIONS.MANAGE_MARKET}
                    token={token}
                >
                    <div className="rounded-lg border border-[#294565] bg-[#1A325F] p-6 shadow">
                        <h3 className="mb-4 text-xl font-bold text-red-400">
                            交易限制設定
                        </h3>

                        <div className="space-y-4">
                            <div>
                                <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                    漲跌停限制 (%)
                                </label>
                                <input
                                    type="number"
                                    step="0.1"
                                    min="0"
                                    max="100"
                                    value={
                                        tradingLimitForm.limitPercent
                                    }
                                    onChange={(e) =>
                                        setTradingLimitForm(
                                            (prev) => ({
                                                ...prev,
                                                limitPercent:
                                                    e.target.value,
                                            }),
                                        )
                                    }
                                    className="w-full rounded border border-[#294565] bg-[#0f203e] p-3 text-white focus:border-[#469FD2] focus:outline-none"
                                    placeholder="例: 10"
                                />
                                <div className="mt-1 text-xs text-[#557797]">
                                    設定每日股價變動的最大百分比限制
                                </div>
                            </div>
                            <PermissionButton
                                requiredPermission={
                                    PERMISSIONS.MANAGE_MARKET
                                }
                                token={token}
                                onClick={handleUpdateTradingLimit}
                                className="w-full rounded bg-red-500 px-4 py-2 text-white hover:bg-red-600"
                            >
                                更新交易限制
                            </PermissionButton>
                        </div>
                    </div>
                </PermissionGuard>

                {/* IPO預設值設定 */}
                <PermissionGuard
                    requiredPermission={PERMISSIONS.MANAGE_MARKET}
                    token={token}
                >
                    <div className="rounded-lg border border-[#294565] bg-[#1A325F] p-6 shadow">
                        <h3 className="mb-4 text-xl font-bold text-green-400">
                            IPO 預設值設定
                        </h3>

                        {ipoDefaults && (
                            <div className="mb-4 rounded border border-[#294565] bg-[#0f203e] p-3">
                                <div className="flex gap-6 text-white">
                                    <div className="flex flex-col items-start">
                                        <span className="mb-1 text-xs text-[#7BC2E6]">
                                            預設股數
                                        </span>
                                        <span className="font-semibold">
                                            {ipoDefaults.defaultInitialShares?.toLocaleString()}
                                        </span>
                                    </div>
                                    <div className="flex flex-col items-start">
                                        <span className="mb-1 text-xs text-[#7BC2E6]">
                                            預設價格
                                        </span>
                                        <span className="font-semibold">
                                            {
                                                ipoDefaults.defaultInitialPrice
                                            }
                                        </span>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="space-y-4">
                            <div>
                                <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                    預設初始股數
                                </label>
                                <input
                                    type="number"
                                    min="1"
                                    value={
                                        ipoDefaultsForm.initialShares
                                    }
                                    onChange={(e) =>
                                        setIpoDefaultsForm(
                                            (prev) => ({
                                                ...prev,
                                                initialShares:
                                                    e.target.value,
                                            }),
                                        )
                                    }
                                    className="w-full rounded border border-[#294565] bg-[#0f203e] p-3 text-white focus:border-[#469FD2] focus:outline-none"
                                    placeholder="例: 1000000"
                                />
                            </div>
                            <div>
                                <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                    預設初始價格 (點)
                                </label>
                                <input
                                    type="number"
                                    min="1"
                                    value={
                                        ipoDefaultsForm.initialPrice
                                    }
                                    onChange={(e) =>
                                        setIpoDefaultsForm(
                                            (prev) => ({
                                                ...prev,
                                                initialPrice:
                                                    e.target.value,
                                            }),
                                        )
                                    }
                                    className="w-full rounded border border-[#294565] bg-[#0f203e] p-3 text-white focus:border-[#469FD2] focus:outline-none"
                                    placeholder="例: 20"
                                />
                            </div>
                            <PermissionButton
                                requiredPermission={
                                    PERMISSIONS.MANAGE_MARKET
                                }
                                token={token}
                                onClick={handleUpdateIpoDefaults}
                                className="w-full rounded bg-green-500 px-4 py-2 text-white hover:bg-green-600"
                            >
                                更新IPO預設值
                            </PermissionButton>
                        </div>
                    </div>
                </PermissionGuard>

                {/* 交易時間設定 */}
                <PermissionGuard
                    requiredPermission={PERMISSIONS.MANAGE_MARKET}
                    token={token}
                >
                    <div className="rounded-lg border border-[#294565] bg-[#1A325F] p-6 shadow">
                        <h3 className="mb-4 text-xl font-bold text-blue-400">
                            🕐 交易時間設定
                        </h3>

                        {tradingHours && tradingHours.openTime && (
                            <div className="mb-4 rounded border border-[#294565] bg-[#0f203e] p-3">
                                <div className="mb-2 text-sm text-[#7BC2E6]">
                                    目前交易時段
                                </div>
                                {tradingHours.openTime.map(
                                    (session, index) => (
                                        <div
                                            key={index}
                                            className="text-sm text-white"
                                        >
                                            時段 {index + 1}:{" "}
                                            {session.start} -{" "}
                                            {session.end} (UTC)
                                        </div>
                                    ),
                                )}
                            </div>
                        )}

                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <span className="text-[#7BC2E6]">
                                    交易時段設定
                                </span>
                                <button
                                    onClick={addTradingSession}
                                    className="rounded bg-blue-500 px-3 py-1 text-sm text-white hover:bg-blue-600"
                                >
                                    + 新增時段
                                </button>
                            </div>

                            {marketTimesForm.openTime.map(
                                (session, index) => (
                                    <div
                                        key={index}
                                        className="flex items-center gap-2 rounded border border-[#294565] bg-[#0f203e] p-3"
                                    >
                                        <div className="flex-1">
                                            <input
                                                type="time"
                                                value={session.start}
                                                onChange={(e) =>
                                                    updateTradingSession(
                                                        index,
                                                        "start",
                                                        e.target
                                                            .value,
                                                    )
                                                }
                                                className="w-full rounded border border-[#294565] bg-[#1A325F] p-2 text-white focus:border-[#469FD2] focus:outline-none"
                                            />
                                        </div>
                                        <span className="text-[#7BC2E6]">
                                            至
                                        </span>
                                        <div className="flex-1">
                                            <input
                                                type="time"
                                                value={session.end}
                                                onChange={(e) =>
                                                    updateTradingSession(
                                                        index,
                                                        "end",
                                                        e.target
                                                            .value,
                                                    )
                                                }
                                                className="w-full rounded border border-[#294565] bg-[#1A325F] p-2 text-white focus:border-[#469FD2] focus:outline-none"
                                            />
                                        </div>
                                        <button
                                            onClick={() =>
                                                removeTradingSession(
                                                    index,
                                                )
                                            }
                                            className="rounded bg-red-500 px-2 py-1 text-sm text-white hover:bg-red-600"
                                        >
                                            刪除
                                        </button>
                                    </div>
                                ),
                            )}

                            <PermissionButton
                                requiredPermission={
                                    PERMISSIONS.MANAGE_MARKET
                                }
                                token={token}
                                onClick={handleUpdateTradingHours}
                                className="w-full rounded bg-blue-500 px-4 py-2 text-white hover:bg-blue-600"
                            >
                                更新交易時間
                            </PermissionButton>
                        </div>

                        <div className="mt-4 text-xs text-[#557797]">
                            * 時間格式為 24 小時制，使用 UTC 時區
                            <br />* 交易時段不可重疊，系統會自動驗證
                        </div>
                    </div>
                </PermissionGuard>
            </div>

            {/* 說明區域 */}
            <div className="rounded-lg border border-[#294565] bg-[#1A325F] p-6 shadow">
                <h3 className="mb-3 text-lg font-bold text-[#92cbf4]">
                    📖 設定說明
                </h3>
                <div className="grid grid-cols-1 gap-4 text-sm text-[#7BC2E6] md:grid-cols-2">
                    <div>
                        <h4 className="mb-2 font-semibold">
                            轉帳手續費
                        </h4>
                        <ul className="space-y-1 text-[#557797]">
                            <li>• 設定使用者轉帳時的手續費率</li>
                            <li>• 最低手續費確保小額轉帳的成本</li>
                            <li>• 修改後立即生效</li>
                        </ul>
                    </div>
                    <div>
                        <h4 className="mb-2 font-semibold">
                            交易限制
                        </h4>
                        <ul className="space-y-1 text-[#557797]">
                            <li>• 設定股價每日漲跌幅限制</li>
                            <li>• 防止價格異常波動</li>
                            <li>• 適用於所有交易訂單</li>
                        </ul>
                    </div>
                    <div>
                        <h4 className="mb-2 font-semibold">
                            IPO預設值
                        </h4>
                        <ul className="space-y-1 text-[#557797]">
                            <li>• 設定重置IPO時的預設參數</li>
                            <li>• 簡化IPO管理流程</li>
                            <li>• 可隨時調整以適應活動需求</li>
                        </ul>
                    </div>
                    <div>
                        <h4 className="mb-2 font-semibold">
                            交易時間
                        </h4>
                        <ul className="space-y-1 text-[#557797]">
                            <li>• 設定市場開放的時間段</li>
                            <li>• 支援多個交易時段</li>
                            <li>• 使用UTC時區，請注意時差</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
};
