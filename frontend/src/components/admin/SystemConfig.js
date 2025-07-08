import { PERMISSIONS } from "@/contexts/PermissionContext";
import {
    getIpoDefaults,
    getIpoStatus,
    resetIpo,
    updateIpo,
    getTradingHours,
    getTransferFeeConfig,
    setTradingLimit,
    updateIpoDefaults,
    updateMarketTimes,
    updateTransferFeeConfig,
    getSystemStats,
} from "@/lib/api";
import { Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { PermissionButton, PermissionGuard } from "./PermissionGuard";
import { TradingHoursVisualizer } from "../trading";

/**
 * 系統設定管理設定
 * 統一管理所有可動態調整的系統參數
 */
export const SystemConfig = ({ token }) => {
    const [notification, setNotification] = useState({
        show: false,
        message: "",
        type: "info",
    });
    const [loading, setLoading] = useState(true);
    const [updating, setUpdating] = useState(false); // 新增：追蹤更新狀態

    // 設定數據
    const [transferFeeConfig, setTransferFeeConfig] = useState(null);
    const [tradingHours, setTradingHours] = useState(null);
    const [ipoDefaults, setIpoDefaults] = useState(null);
    const [ipoStatus, setIpoStatus] = useState(null);
    const [systemStats, setSystemStats] = useState(null);

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
    const [ipoUpdateForm, setIpoUpdateForm] = useState({
        sharesRemaining: "",
        initialPrice: "",
    });

    // 顯示通知
    const showNotification = (message, type = "info") => {
        setNotification({ show: true, message, type });
        
        // 成功時添加觸覺反饋（如果支持）
        if (type === "success" && "vibrate" in navigator) {
            navigator.vibrate([100, 50, 100]); // 短-停-短震動模式
        }
        
        // 成功訊息顯示更久一點，錯誤訊息也顯示久一點
        const duration = type === "success" ? 6000 : type === "error" ? 7000 : 4000;
        
        setTimeout(
            () =>
                setNotification({
                    show: false,
                    message: "",
                    type: "info",
                }),
            duration,
        );
    };

    // 載入所有設定
    const loadConfigs = async () => {
        try {
            setLoading(true);

            // 並行載入所有設定
            const [feeConfig, hours, defaults, ipoCurrentStatus, stats] =
                await Promise.allSettled([
                    getTransferFeeConfig(token),
                    getTradingHours(),
                    getIpoDefaults(token),
                    getIpoStatus(token),
                    getSystemStats(token),
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
                if (
                    hours.value.tradingHours &&
                    hours.value.tradingHours.length > 0
                ) {
                    const formattedTimes =
                        hours.value.tradingHours.map((slot) => {
                            // 使用 UTC 時間戳，轉換為台北時間 (UTC+8)
                            const startDate = new Date(slot.start * 1000);
                            const endDate = new Date(slot.end * 1000);
                            
                            // 格式化為 HH:MM，確保時區正確
                            const startTime = startDate.toLocaleTimeString('en-GB', {
                                timeZone: 'Asia/Taipei',
                                hour12: false,
                                hour: '2-digit',
                                minute: '2-digit'
                            });
                            const endTime = endDate.toLocaleTimeString('en-GB', {
                                timeZone: 'Asia/Taipei', 
                                hour12: false,
                                hour: '2-digit',
                                minute: '2-digit'
                            });
                            
                            return {
                                start: startTime,
                                end: endTime,
                            };
                        });
                    setMarketTimesForm({
                        openTime: formattedTimes,
                    });
                } else {
                    setMarketTimesForm({
                        openTime: hours.value.openTime || [],
                    });
                }
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

            if (ipoCurrentStatus.status === "fulfilled") {
                setIpoStatus(ipoCurrentStatus.value);
                setIpoUpdateForm({
                    sharesRemaining: ipoCurrentStatus.value.sharesRemaining || "",
                    initialPrice: ipoCurrentStatus.value.initialPrice || "",
                });
            }

            if (stats.status === "fulfilled") {
                setSystemStats(stats.value);
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

            setUpdating(true); // 開始更新

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
        } finally {
            setUpdating(false); // 結束更新
        }
    };

    // 更新交易限制
    const handleUpdateTradingLimit = async () => {
        try {
            if (!tradingLimitForm.limitPercent) {
                showNotification("請填寫交易限制百分比", "error");
                return;
            }

            setUpdating(true); // 開始更新

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
        } finally {
            setUpdating(false); // 結束更新
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

            setUpdating(true); // 開始更新

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
        } finally {
            setUpdating(false); // 結束更新
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

    // 更新IPO狀態
    const handleUpdateIpoStatus = async () => {
        try {
            const sharesRemaining =
                ipoUpdateForm.sharesRemaining !== ""
                    ? parseInt(ipoUpdateForm.sharesRemaining)
                    : null;
            const initialPrice =
                ipoUpdateForm.initialPrice !== ""
                    ? parseInt(ipoUpdateForm.initialPrice)
                    : null;

            setUpdating(true); // 開始更新

            const result = await updateIpo(
                token,
                sharesRemaining,
                initialPrice,
            );

            showNotification(result.message, "success");
            await loadConfigs(); // 重新載入設定
        } catch (error) {
            showNotification(
                `更新IPO狀態失敗: ${error.message}`,
                "error",
            );
        } finally {
            setUpdating(false); // 結束更新
        }
    };

    // 重置IPO
    const handleResetIpo = async () => {
        try {
            if (confirm("確定要重置IPO嗎？這將使用預設值重新開始IPO。")) {
                setUpdating(true); // 開始更新

                const result = await resetIpo(token);
                showNotification(result.message, "success");
                await loadConfigs(); // 重新載入設定
            }
        } catch (error) {
            showNotification(
                `重置IPO失敗: ${error.message}`,
                "error",
            );
        } finally {
            setUpdating(false); // 結束更新
        }
    };

    // 儲存交易時間
    const handleUpdateTradingHours = async () => {
        if (updating) return; // 防止重複提交
        
        try {
            setUpdating(true); // 在開始時就設置更新狀態
            
            // 驗證時間格式
            const validSessions = marketTimesForm.openTime.filter(
                (session) => session.start && session.end,
            );

            if (validSessions.length === 0) {
                showNotification("請至少設定一個交易時段", "error");
                return;
            }

            const openTime = validSessions.map((time) => {
                const today = new Date();
                const startTime = new Date(
                    today.toDateString() + " " + time.start,
                );
                const endTime = new Date(
                    today.toDateString() + " " + time.end,
                );

                const result = {
                    start: Math.floor(startTime.getTime() / 1000),
                    end: Math.floor(endTime.getTime() / 1000),
                };
                
                console.log(`Time ${time.start}-${time.end} converted to:`, result);
                console.log(`Readable: ${new Date(result.start * 1000).toLocaleString('zh-TW', {timeZone: 'Asia/Taipei'})} - ${new Date(result.end * 1000).toLocaleString('zh-TW', {timeZone: 'Asia/Taipei'})}`);
                
                return result;
            });

            console.log('Sending openTime to API:', openTime);
            await updateMarketTimes(token, openTime);
            
            // 顯示更詳細的成功訊息
            const timeRanges = validSessions.map(session => `${session.start}-${session.end}`).join(', ');
            showNotification(`交易時間更新成功！新的交易時段：${timeRanges}`, "success");
            
            // 直接更新 tradingHours 狀態，避免重新載入導致表單重置
            setTradingHours({
                tradingHours: openTime
            });
        } catch (error) {
            showNotification(
                `更新交易時間失敗: ${error.message}`,
                "error",
            );
        } finally {
            setUpdating(false); // 結束更新
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
        <div className="relative space-y-8">
            {/* 固定在螢幕頂部的通知區域 */}
            {notification.show && (
                <div className="fixed left-1/2 top-4 z-50 w-full max-w-md -translate-x-1/2 transform px-4">
                    <div
                        className={`animate-in slide-in-from-top-2 fade-in-0 duration-300 rounded-lg border p-4 shadow-xl backdrop-blur-sm ${
                            notification.type === "success"
                                ? "border-green-500/50 bg-green-600/90 text-green-100 shadow-green-500/30"
                                : notification.type === "error"
                                  ? "border-red-500/50 bg-red-600/90 text-red-100 shadow-red-500/30"
                                  : "border-blue-500/50 bg-blue-600/90 text-blue-100 shadow-blue-500/30"
                        }`}
                    >
                        <div className="flex items-center justify-between space-x-2">
                            <div className="flex items-center space-x-2">
                                {notification.type === "success" && (
                                    <svg className="h-5 w-5 text-green-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                )}
                                {notification.type === "error" && (
                                    <svg className="h-5 w-5 text-red-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                )}
                                {notification.type === "info" && (
                                    <svg className="h-5 w-5 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                )}
                                <span className="font-medium text-sm">{notification.message}</span>
                            </div>
                            <button
                                onClick={() => setNotification({ show: false, message: "", type: "info" })}
                                className="text-current opacity-70 hover:opacity-100 transition-opacity ml-2 flex-shrink-0"
                            >
                                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* 系統數值統計 */}
            {systemStats && (
                <div className="rounded-lg border border-[#294565] bg-[#1A325F] p-6 shadow mb-8">
                    <div className="mb-4 flex items-center justify-between">
                        <h3 className="text-xl font-bold text-[#92cbf4]">
                            📊 目前系統數值
                        </h3>
                        <button
                            onClick={loadConfigs}
                            disabled={loading}
                            className="rounded bg-[#469FD2] px-3 py-1 text-sm text-white hover:bg-[#357AB8] disabled:opacity-50"
                        >
                            {loading ? "更新中..." : "刷新數據"}
                        </button>
                    </div>
                    <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
                        <div className="rounded border border-[#294565] bg-[#0f203e] p-4 text-center">
                            <div className="text-2xl font-bold text-green-400">
                                {systemStats.total_points?.toLocaleString() || 0}
                            </div>
                            <div className="text-sm text-[#7BC2E6]">總點數</div>
                        </div>
                        <div className="rounded border border-[#294565] bg-[#0f203e] p-4 text-center">
                            <div className="text-2xl font-bold text-blue-400">
                                {systemStats.total_stocks?.toLocaleString() || 0}
                            </div>
                            <div className="text-sm text-[#7BC2E6]">總股數</div>
                        </div>
                        <div className="rounded border border-[#294565] bg-[#0f203e] p-4 text-center">
                            <div className="text-2xl font-bold text-yellow-400">
                                {systemStats.total_users?.toLocaleString() || 0}
                            </div>
                            <div className="text-sm text-[#7BC2E6]">使用者數</div>
                        </div>
                        <div className="rounded border border-[#294565] bg-[#0f203e] p-4 text-center">
                            <div className="text-2xl font-bold text-purple-400">
                                {systemStats.total_groups?.toLocaleString() || 0}
                            </div>
                            <div className="text-sm text-[#7BC2E6]">隊伍數</div>
                        </div>
                        <div className="rounded border border-[#294565] bg-[#0f203e] p-4 text-center">
                            <div className="text-2xl font-bold text-orange-400">
                                {systemStats.total_trades?.toLocaleString() || 0}
                            </div>
                            <div className="text-sm text-[#7BC2E6]">成交次數</div>
                        </div>
                    </div>
                    {systemStats.generated_at && (
                        <div className="mt-4 text-xs text-gray-400 text-center">
                            最後更新：{new Date(systemStats.generated_at).toLocaleString('zh-TW')}
                        </div>
                    )}
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
                                                transferFeeConfig.fee_rate || transferFeeConfig.feeRate || 'N/A'
                                            }
                                            %
                                        </span>
                                    </div>
                                    <div className="flex flex-col items-start">
                                        <span className="mb-1 text-xs text-[#7BC2E6]">
                                            最低費用
                                        </span>
                                        <span className="font-semibold">
                                            {transferFeeConfig.min_fee || transferFeeConfig.minFee || 'N/A'}{" "}
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
                                            {(ipoDefaults.default_initial_shares || ipoDefaults.defaultInitialShares)?.toLocaleString() || 'N/A'}
                                        </span>
                                    </div>
                                    <div className="flex flex-col items-start">
                                        <span className="mb-1 text-xs text-[#7BC2E6]">
                                            預設價格
                                        </span>
                                        <span className="font-semibold">
                                            {
                                                ipoDefaults.default_initial_price || ipoDefaults.defaultInitialPrice || 'N/A'
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

                {/* IPO 狀態管理 */}
                <PermissionGuard
                    requiredPermission={PERMISSIONS.MANAGE_MARKET}
                    token={token}
                >
                    <div className="rounded-lg border border-[#294565] bg-[#1A325F] p-6 shadow">
                        <h3 className="mb-4 text-xl font-bold text-purple-400">
                            IPO 狀態管理
                        </h3>

                        {/* 當前IPO狀態顯示 */}
                        {ipoStatus && (
                            <div className="mb-4 rounded border border-[#294565] bg-[#0f203e] p-4">
                                <h4 className="mb-3 text-sm font-medium text-[#7BC2E6]">
                                    當前 IPO 狀態
                                </h4>
                                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                                    <div className="text-center">
                                        <div className="text-xs text-[#7BC2E6]">剩餘股數</div>
                                        <div className="text-lg font-semibold text-white">
                                            {ipoStatus.sharesRemaining?.toLocaleString() || 'N/A'}
                                        </div>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-xs text-[#7BC2E6]">IPO 價格</div>
                                        <div className="text-lg font-semibold text-white">
                                            {ipoStatus.initialPrice || 'N/A'} 點
                                        </div>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-xs text-[#7BC2E6]">狀態</div>
                                        <div className={`inline-block rounded-full px-3 py-1 text-sm font-medium ${
                                            (ipoStatus.sharesRemaining || 0) > 0 
                                                ? "bg-green-600 text-green-100"
                                                : "bg-red-600 text-red-100"
                                        }`}>
                                            {(ipoStatus.sharesRemaining || 0) > 0 ? "進行中" : "已結束"}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="space-y-4">
                            <div>
                                <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                    剩餘股數 (留空則不更新)
                                </label>
                                <input
                                    type="number"
                                    min="0"
                                    value={ipoUpdateForm.sharesRemaining}
                                    onChange={(e) =>
                                        setIpoUpdateForm((prev) => ({
                                            ...prev,
                                            sharesRemaining: e.target.value,
                                        }))
                                    }
                                    className="w-full rounded border border-[#294565] bg-[#0f203e] p-3 text-white focus:border-[#469FD2] focus:outline-none"
                                    placeholder="例: 500000"
                                />
                            </div>
                            <div>
                                <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                    IPO 價格 (留空則不更新)
                                </label>
                                <input
                                    type="number"
                                    min="1"
                                    value={ipoUpdateForm.initialPrice}
                                    onChange={(e) =>
                                        setIpoUpdateForm((prev) => ({
                                            ...prev,
                                            initialPrice: e.target.value,
                                        }))
                                    }
                                    className="w-full rounded border border-[#294565] bg-[#0f203e] p-3 text-white focus:border-[#469FD2] focus:outline-none"
                                    placeholder="例: 25"
                                />
                            </div>
                            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                                <PermissionButton
                                    requiredPermission={PERMISSIONS.MANAGE_MARKET}
                                    token={token}
                                    onClick={handleUpdateIpoStatus}
                                    className="w-full rounded bg-purple-500 px-4 py-2 text-white hover:bg-purple-600"
                                >
                                    更新 IPO 狀態
                                </PermissionButton>
                                <PermissionButton
                                    requiredPermission={PERMISSIONS.MANAGE_MARKET}
                                    token={token}
                                    onClick={handleResetIpo}
                                    className="w-full rounded bg-yellow-500 px-4 py-2 text-white hover:bg-yellow-600"
                                >
                                    重置 IPO
                                </PermissionButton>
                            </div>
                            <div className="rounded-lg border border-purple-600 bg-purple-900/20 p-3">
                                <p className="text-sm text-purple-200">
                                    💡 提示：
                                    <br />• 設定剩餘股數為 0 可停止 IPO 發行
                                    <br />• 重置 IPO 會使用預設值重新開始
                                    <br />• 空白欄位將不會更新對應值
                                </p>
                            </div>
                        </div>
                    </div>
                </PermissionGuard>

                {/* 交易時間設定 */}
                <PermissionGuard
                    requiredPermission={PERMISSIONS.MANAGE_MARKET}
                    token={token}
                >
                    <div className="rounded-lg border border-[#294565] bg-[#1A325F] p-6 shadow">
                        <div className="space-y-4">
                            <div className="flex place-items-center justify-between">
                                <h3 className="text-xl font-bold text-blue-400">
                                    交易時間設定
                                </h3>
                                <button
                                    onClick={addTradingSession}
                                    className="flex items-center space-x-2 rounded-lg bg-blue-500 px-3 py-2 text-sm text-white transition-colors hover:bg-blue-600"
                                >
                                    <span>新增時段</span>
                                </button>
                            </div>

                            {marketTimesForm.openTime.length === 0 ? (
                                <div className="rounded-lg border-2 border-dashed border-[#294565] bg-[#0f203e] p-6 text-center">
                                    <div className="text-[#7BC2E6]">
                                        <Plus className="mx-auto h-12 w-12" />
                                        <p className="text-sm">
                                            尚未設定交易時段
                                        </p>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {marketTimesForm.openTime.map(
                                        (session, index) => (
                                            <div
                                                key={index}
                                                className="rounded-lg border border-[#294565] bg-[#0f203e] p-4"
                                            >
                                                <div className="mb-3 flex items-center justify-between">
                                                    <div className="flex items-center space-x-2">
                                                        <span className="font-medium text-white">
                                                            交易時段{" "}
                                                            {index +
                                                                1}
                                                        </span>
                                                    </div>
                                                    <button
                                                        onClick={() =>
                                                            removeTradingSession(
                                                                index,
                                                            )
                                                        }
                                                        className="flex items-center space-x-1 rounded bg-red-500 px-3 py-1 text-sm text-white transition-colors hover:bg-red-600"
                                                    >
                                                        <span>
                                                            刪除
                                                        </span>
                                                    </button>
                                                </div>

                                                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                                                    <div>
                                                        <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                                            開始時間
                                                        </label>
                                                        <input
                                                            type="time"
                                                            value={
                                                                session.start
                                                            }
                                                            onChange={(
                                                                e,
                                                            ) =>
                                                                updateTradingSession(
                                                                    index,
                                                                    "start",
                                                                    e
                                                                        .target
                                                                        .value,
                                                                )
                                                            }
                                                            className="w-full rounded-lg border border-[#294565] bg-[#1A325F] p-3 text-white focus:border-[#469FD2] focus:outline-none"
                                                        />
                                                    </div>
                                                    <div>
                                                        <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                                            結束時間
                                                        </label>
                                                        <input
                                                            type="time"
                                                            value={
                                                                session.end
                                                            }
                                                            onChange={(
                                                                e,
                                                            ) =>
                                                                updateTradingSession(
                                                                    index,
                                                                    "end",
                                                                    e
                                                                        .target
                                                                        .value,
                                                                )
                                                            }
                                                            className="w-full rounded-lg border border-[#294565] bg-[#1A325F] p-3 text-white focus:border-[#469FD2] focus:outline-none"
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        ),
                                    )}
                                </div>
                            )}

                            <TradingHoursVisualizer
                                tradingHours={tradingHours}
                                marketTimesForm={marketTimesForm}
                            />

                            <PermissionButton
                                requiredPermission={
                                    PERMISSIONS.MANAGE_MARKET
                                }
                                token={token}
                                onClick={handleUpdateTradingHours}
                                disabled={
                                    updating || marketTimesForm.openTime.length === 0
                                }
                                className={`w-full rounded px-4 py-2 font-medium text-white transition-all duration-200 disabled:cursor-not-allowed disabled:bg-gray-600 disabled:text-gray-400 ${
                                    updating 
                                        ? 'bg-blue-400 cursor-wait' 
                                        : 'bg-blue-500 hover:bg-blue-600 hover:shadow-lg'
                                }`}
                            >
                                {updating ? (
                                    <div className="flex items-center justify-center space-x-2">
                                        <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        <span>更新中...</span>
                                    </div>
                                ) : (
                                    "更新交易時間"
                                )}
                            </PermissionButton>
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
                            IPO狀態管理
                        </h4>
                        <ul className="space-y-1 text-[#557797]">
                            <li>• 即時調整當前IPO的剩餘股數和價格</li>
                            <li>• 可以停止或重新開始IPO發行</li>
                            <li>• 重置功能會使用預設值重新初始化</li>
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
