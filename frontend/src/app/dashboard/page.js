"use client";

import {
    cancelWebStockOrder,
    getWebPointHistory,
    getWebPortfolio,
    getWebStockOrders,
    getMyPermissions,
} from "@/lib/api";
import Modal from "@/components/Modal";
import dayjs from "dayjs";
import { LogOut } from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { twMerge } from "tailwind-merge";

export default function Dashboard() {
    const [isLoading, setIsLoading] = useState(true);
    const [user, setUser] = useState(null);
    const [studentList, setStudentList] = useState([]);
    const [pointHistory, setPointHistory] = useState([]);
    const [pointHistoryPage, setPointHistoryPage] = useState(0);
    const [orderHistory, setOrderHistory] = useState([]);
    const [orderHistoryPage, setOrderHistoryPage] = useState(0);
    const [authData, setAuthData] = useState(null);
    const [activeTab, setActiveTab] = useState("portfolio");
    const [error, setError] = useState("");
    const [cancelingOrders, setCancelingOrders] = useState(new Set());
    const [cancelSuccess, setCancelSuccess] = useState("");
    const [cancelError, setCancelError] = useState("");
    const [showCancelModal, setShowCancelModal] = useState(false);
    const [pendingCancelOrder, setPendingCancelOrder] = useState(null);
    const [userPermissions, setUserPermissions] = useState(null);
    const router = useRouter();

    // 登出功能
    const handleLogout = () => {
        localStorage.removeItem("isUser");
        localStorage.removeItem("userToken");
        localStorage.removeItem("userData");
        localStorage.removeItem("telegramData");
        router.push("/telegram-login");
    };

    // 開啟取消訂單 Modal
    const openCancelModal = (orderData, orderType, quantity) => {
        // 從訂單物件中提取正確的 ID - 嘗試更多可能的字段
        const orderId =
            orderData._id ||
            orderData.id ||
            orderData.order_id ||
            orderData.orderId ||
            orderData["$oid"];

        console.log("=== 取消訂單Debug訊息 ===");
        console.log("完整訂單資料:", orderData);
        console.log("訂單物件的所有 keys:", Object.keys(orderData));
        console.log("嘗試提取的 ID:", orderId);
        console.log("ID 類型:", typeof orderId);
        console.log("訂單的使用者ID:", orderData.user_id);
        console.log("目前使用者資料:", user);

        // 從 localStorage 獲取真正的 telegram ID
        const telegramDataStr = localStorage.getItem("telegramData");
        const userDataStr = localStorage.getItem("userData");
        let telegramData = null;
        let userData = null;

        try {
            telegramData = JSON.parse(telegramDataStr);
            userData = JSON.parse(userDataStr);
        } catch (e) {
            console.error("無法解析 localStorage 數據:", e);
        }

        console.log("解析後的 telegramData:", telegramData);
        console.log("解析後的 userData:", userData);
        console.log("真正的 Telegram ID:", telegramData?.id);
        console.log("內部 User ID:", userData?.id);
        console.log("========================");

        if (!orderId) {
            console.error("無法從訂單物件中找到有效的 ID 字段");
            setCancelError("無法取得訂單 ID - 請檢查控制台Debug訊息");
            return;
        }

        setPendingCancelOrder({
            orderData,
            orderType,
            quantity,
            orderId
        });
        setShowCancelModal(true);
    };

    // 確認取消訂單
    const confirmCancelOrder = async () => {
        if (!pendingCancelOrder) return;

        const { orderData, orderType, quantity, orderId } = pendingCancelOrder;

        const token = localStorage.getItem("userToken");
        if (!token) {
            setCancelError("認證已過期，請重新登入");
            setShowCancelModal(false);
            setPendingCancelOrder(null);
            return;
        }

        // 關閉 Modal
        setShowCancelModal(false);

        // 添加到取消中的訂單集合
        setCancelingOrders((prev) => new Set(prev).add(orderId));
        setCancelError("");
        setCancelSuccess("");

        try {
            const result = await cancelWebStockOrder(
                token,
                orderId,
                "使用者主動取消",
            );

            if (result.success) {
                setCancelSuccess("訂單已成功取消");

                // 重新載入訂單歷史
                try {
                    const updatedOrders =
                        await getWebStockOrders(token);
                    setOrderHistory(updatedOrders);
                } catch (refreshError) {
                    console.error("重新載入訂單失敗:", refreshError);
                }

                // 3秒後清除成功訊息
                setTimeout(() => setCancelSuccess(""), 3000);
            } else {
                setCancelError(result.message || "取消訂單失敗");
            }
        } catch (error) {
            console.error("取消訂單失敗:", error);
            setCancelError(error.message || "取消訂單時發生錯誤");
        } finally {
            // 從取消中的訂單集合移除
            setCancelingOrders((prev) => {
                const newSet = new Set(prev);
                newSet.delete(orderId);
                return newSet;
            });
            setPendingCancelOrder(null);
        }
    };

    // 關閉取消 Modal
    const closeCancelModal = () => {
        setShowCancelModal(false);
        setPendingCancelOrder(null);
    };

    // 檢查訂單是否可以取消
    const canCancelOrder = (order) => {
        const cancellableStatuses = [
            "pending",
            "partial",
            "pending_limit",
        ];
        return (
            cancellableStatuses.includes(order.status) &&
            order.quantity > 0
        );
    };

    // 檢查登入狀態並載入使用者資料
    useEffect(() => {
        const checkAuthAndLoadData = async () => {
            // 檢查必要的認證資料
            const isUser = localStorage.getItem("isUser");
            const token = localStorage.getItem("userToken");
            const telegramData = localStorage.getItem("telegramData");

            console.log("認證檢查:", {
                isUser,
                hasToken: !!token,
                hasTelegramData: !!telegramData,
            });

            // 如果缺少任何必要的認證資料，重新導向到登入頁
            if (!isUser || !token || !telegramData) {
                console.log("缺少認證資料，重新導向到登入頁");
                handleLogout(); // 清理可能不完整的資料
                return;
            }

            // 檢查 token 格式是否正確
            try {
                const tokenParts = token.split(".");
                if (tokenParts.length !== 3) {
                    console.log("Token 格式無效");
                    handleLogout();
                    return;
                }
            } catch (e) {
                console.log("Token 驗證失敗");
                handleLogout();
                return;
            }

            try {
                // 設定 Telegram 資料
                let parsedTelegramData = null;
                try {
                    parsedTelegramData = JSON.parse(telegramData);
                    // 檢查是否為有效的 Telegram 登入資料
                    if (
                        !parsedTelegramData ||
                        typeof parsedTelegramData !== "object"
                    ) {
                        throw new Error(
                            "Invalid telegram data structure",
                        );
                    }
                } catch (parseError) {
                    console.log(
                        "Telegram 資料無效，可能未使用 Telegram 登入:",
                        parseError,
                    );
                    // 如果是無效的 Telegram 資料，引導重新登入
                    setError("請使用 Telegram 登入以獲得完整功能");
                    setTimeout(() => {
                        handleLogout();
                    }, 3000);
                    return;
                }
                setAuthData(parsedTelegramData);

                console.log("開始載入使用者資料...");

                // 載入使用者資料
                const [portfolio, points, stocks, permissions] = await Promise.all(
                    [
                        getWebPortfolio(token),
                        getWebPointHistory(token),
                        getWebStockOrders(token),
                        getMyPermissions(token).catch((error) => {
                            console.warn("無法載入權限資訊:", error);
                            return null;
                        }),
                    ],
                );

                console.log("資料載入成功:", {
                    portfolio,
                    pointsCount: points.length,
                    stocksCount: stocks.length,
                    permissions,
                });

                setUser(portfolio);
                setPointHistory(points);
                setOrderHistory(stocks);
                setUserPermissions(permissions);
                setIsLoading(false);
            } catch (error) {
                console.error("載入使用者資料失敗:", error);

                // 處理不同類型的錯誤
                if (error.status === 401 || error.status === 403) {
                    console.log("認證失敗，重新登入");
                    handleLogout();
                } else if (error.status === 404) {
                    console.log("使用者未註冊或資料不存在");
                    setError(
                        "使用者帳號未完成註冊，或需要使用 Telegram 登入。將重新導向到登入頁面...",
                    );
                    setTimeout(() => {
                        handleLogout();
                    }, 3000);
                    setIsLoading(false);
                } else if (error.status >= 500) {
                    console.log("伺服器錯誤");
                    setError("伺服器暫時無法使用，請稍後再試");
                    setIsLoading(false);
                } else {
                    console.log("其他錯誤:", error);
                    setError("載入資料失敗，請重新整理頁面");
                    setIsLoading(false);
                }
            }
        };

        checkAuthAndLoadData();
    }, [router]);

    if (isLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-[#0f203e]">
                <div className="text-center">
                    <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-[#92cbf4] border-t-transparent"></div>
                    <p className="text-[#92cbf4]">載入中...</p>
                </div>
            </div>
        );
    }

    // 如果有錯誤且不是載入中，顯示錯誤頁面
    if (error && !isLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-[#0f203e]">
                <div className="max-w-md p-6 text-center">
                    <div className="mb-4 text-6xl">⚠️</div>
                    <h2 className="mb-4 text-xl font-bold text-red-400">
                        載入失敗
                    </h2>
                    <p className="mb-6 text-[#92cbf4]">{error}</p>
                    <div className="space-y-3">
                        <button
                            onClick={() => window.location.reload()}
                            className="w-full rounded-lg bg-[#469FD2] px-4 py-2 text-white transition-colors hover:bg-[#357AB8]"
                        >
                            重新載入
                        </button>
                        <button
                            onClick={handleLogout}
                            className="w-full rounded-lg border border-[#294565] px-4 py-2 text-[#92cbf4] transition-colors hover:bg-[#1A325F]"
                        >
                            重新登入
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // 確保必要資料存在才渲染主要內容
    if (!user || !authData) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-[#0f203e]">
                <div className="text-center">
                    <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-[#92cbf4] border-t-transparent"></div>
                    <p className="text-[#92cbf4]">準備資料中...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex min-h-screen w-full bg-[#0f203e] pt-10 pb-20 md:items-center">
            <div className="w-full space-y-4 p-4">
                <div className="mx-auto flex max-w-2xl space-x-8 rounded-lg border border-[#294565] bg-[#1A325F] p-6">
                    {authData?.photo_url ? (
                        <Image
                            src={authData.photo_url}
                            alt="Telegram 頭貼"
                            width={80}
                            height={80}
                            className="h-20 w-20 rounded-full"
                        />
                    ) : (
                        <div className="inline-flex h-20 w-20 items-center justify-center rounded-full bg-[#264173] text-xl font-bold text-[#92cbf4]">
                            {user?.username
                                ?.substring(0, 1)
                                ?.toUpperCase() || "U"}
                        </div>
                    )}
                    <div>
                        <p className="mb-2 text-xl">
                            早安，
                            <b>{user?.username || "使用者"}</b>
                        </p>
                        <p className="mb-1 text-[#92cbf4]">
                            你現在擁有的總資產為{" "}
                            <span className="text-white">
                                {user?.totalValue?.toLocaleString() ||
                                    "0"}
                            </span>{" "}
                            點
                        </p>
                        <p className="text-sm text-[#92cbf4]">
                            可動用點數共{" "}
                            <span className="text-white">
                                {user?.points?.toLocaleString() ||
                                    "0"}
                            </span>{" "}
                            點
                        </p>
                    </div>
                    <div className="ml-auto">
                        <button onClick={handleLogout}>
                            <LogOut className="h-5 w-5 text-[#92cbf4] transition-colors hover:text-red-700" />
                        </button>
                    </div>
                </div>

                <div className="mx-auto max-w-2xl rounded-lg border border-[#294565] bg-[#1A325F] p-6">
                    <h3 className="mb-4 text-lg font-semibold text-[#92cbf4]">
                        資產總覽
                    </h3>
                    <div className="grid grid-cols-2 place-items-center gap-4 md:grid-cols-4">
                        <div>
                            <p className="mb-1 text-center text-sm text-[#557797]">
                                現金點數
                            </p>
                            <p className="text-center text-xl font-bold text-white">
                                {user?.points?.toLocaleString() ||
                                    "0"}
                            </p>
                        </div>
                        <div>
                            <p className="mb-1 text-center text-sm text-[#557797]">
                                股票數量
                            </p>
                            <p className="text-center text-xl font-bold text-white">
                                {user?.stocks?.toLocaleString() ||
                                    "0"}
                            </p>
                        </div>
                        <div>
                            <p className="mb-1 text-center text-sm text-[#557797]">
                                股票價值
                            </p>
                            <p className="text-center text-xl font-bold text-white">
                                {user?.stockValue?.toLocaleString() ||
                                    "0"}
                            </p>
                        </div>
                        <div>
                            <p className="mb-1 text-center text-sm text-[#557797]">
                                總資產
                            </p>
                            <p className="text-center text-xl font-bold text-[#92cbf4]">
                                {user?.totalValue?.toLocaleString() ||
                                    "0"}
                            </p>
                        </div>
                    </div>
                    {user?.avgCost !== undefined && (
                        <div className="mt-4 border-t border-[#294565] pt-4">
                            <p className="text-sm text-[#557797]">
                                購買股票平均成本:{" "}
                                <span className="font-semibold text-white">
                                    {user.avgCost}
                                </span>
                            </p>
                        </div>
                    )}
                </div>

                {/* 權限資訊 */}
                {userPermissions && (
                    <div className="mx-auto max-w-2xl rounded-lg border border-[#294565] bg-[#1A325F] p-6">
                        <h3 className="mb-4 text-lg font-semibold text-[#92cbf4]">
                            帳號權限資訊
                        </h3>
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-[#557797]">角色</span>
                                <span className="rounded bg-[#294565] px-2 py-1 text-sm font-medium text-[#92cbf4]">
                                    {userPermissions.role === 'student' && '一般學員'}
                                    {userPermissions.role === 'point_manager' && '點數管理員'}
                                    {userPermissions.role === 'announcer' && '公告員'}
                                    {userPermissions.role === 'admin' && '系統管理員'}
                                    {!['student', 'point_manager', 'announcer', 'admin'].includes(userPermissions.role) && userPermissions.role}
                                </span>
                            </div>
                            
                            <div>
                                <p className="mb-2 text-sm text-[#557797]">可用權限</p>
                                <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                                    {userPermissions.permissions && userPermissions.permissions.length > 0 ? (
                                        userPermissions.permissions.map((permission, index) => (
                                            <div key={index} className="flex items-center space-x-2">
                                                <span className="text-green-400">✓</span>
                                                <span className="text-xs text-white">
                                                    {permission === 'view_own_data' && '查看自己的資料'}
                                                    {permission === 'trade_stocks' && '股票交易'}
                                                    {permission === 'transfer_points' && '轉帳點數'}
                                                    {permission === 'view_all_users' && '查看所有使用者'}
                                                    {permission === 'give_points' && '發放點數'}
                                                    {permission === 'create_announcement' && '發布公告'}
                                                    {permission === 'manage_users' && '管理使用者'}
                                                    {permission === 'manage_market' && '管理市場'}
                                                    {permission === 'system_admin' && '系統管理'}
                                                    {!['view_own_data', 'trade_stocks', 'transfer_points', 'view_all_users', 'give_points', 'create_announcement', 'manage_users', 'manage_market', 'system_admin'].includes(permission) && permission}
                                                </span>
                                            </div>
                                        ))
                                    ) : (
                                        <p className="text-xs text-[#557797]">暫無特殊權限</p>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* TODO: Blocked due to API */}
                {/*<div className="mx-auto flex max-w-2xl space-x-8 rounded-lg border border-[#294565] bg-[#1A325F] p-6">
                    <div className="relative">
                        <input
                            type="text"
                            // value={givePointsForm.username}
                            // onChange={(e) =>
                            //     // handleUsernameChange(
                            //     //     e.target.value,
                            //     // )
                            // }
                            onFocus={() => {
                                // 重新觸發搜尋以顯示建議
                                // if (
                                //     givePointsForm.username.trim() !==
                                //     ""
                                // ) {
                                //     handleUsernameChange(
                                //         givePointsForm.username,
                                //     );
                                // }
                            }}
                            onBlur={() => {
                                // 延遲隱藏建議，讓點選事件能夠觸發
                                // setTimeout(
                                //     () =>
                                //         setShowSuggestions(
                                //             false,
                                //         ),
                                //     200,
                                // );
                            }}
                            // disabled={studentsLoading}
                            className="w-full rounded-xl border border-[#469FD2] bg-[#1A325F] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none disabled:cursor-not-allowed disabled:bg-[#0f203e] disabled:opacity-50"
                            placeholder={"正在載入使用者資料..."}
                        />
                        {showSuggestions &&
                            suggestions.length > 0 && (
                                <div className="absolute z-10 mt-1 max-h-48 w-full overflow-y-auto rounded-xl border border-[#469FD2] bg-[#0f203e] shadow-lg">
                                    {suggestions.map(
                                        (suggestion, index) => (
                                            <div
                                                key={index}
                                                onMouseDown={(e) => {
                                                    e.preventDefault(); // 防止blur事件影響點選
                                                    if (
                                                        givePointsForm.type.startsWith(
                                                            "multi_",
                                                        )
                                                    ) {
                                                        addMultiTarget(
                                                            suggestion,
                                                        );
                                                    } else {
                                                        selectSuggestion(
                                                            suggestion,
                                                        );
                                                    }
                                                }}
                                                className="cursor-pointer border-b border-[#469FD2] px-3 py-2 text-sm text-white transition-colors last:border-b-0 hover:bg-[#1A325F]"
                                            >
                                                <div className="flex items-center justify-between">
                                                    <span>
                                                        {
                                                            suggestion.label
                                                        }
                                                    </span>
                                                    <span className="text-xs text-gray-400">
                                                        {suggestion.type ===
                                                        "user"
                                                            ? "個人"
                                                            : "團隊"}
                                                    </span>
                                                </div>
                                            </div>
                                        ),
                                    )}
                                </div>
                            )}
                    </div>
                </div>*/}

                <div className="mx-auto max-w-2xl rounded-lg border border-[#294565] bg-[#1A325F] p-6">
                    <h3 className="mb-4 text-lg font-semibold text-[#92cbf4]">
                        點數紀錄
                    </h3>

                    <div className="grid grid-flow-row gap-4">
                        {pointHistory && pointHistory.length > 0 ? (
                            pointHistory.map((i) => {
                                return (
                                    <div
                                        className="grid grid-cols-5 space-y-1 md:space-y-0 md:space-x-4"
                                        key={i.created_at}
                                    >
                                        <p className="col-span-5 font-mono text-sm md:col-span-1 md:text-base">
                                            {dayjs(
                                                i.created_at,
                                            ).add(8, "hour").format("MM/DD HH:mm")}
                                        </p>
                                        <div className="col-span-5 md:col-span-4 md:flex">
                                            <p className="font-bold text-[#92cbf4]">
                                                {i.note}
                                            </p>

                                            <p className="ml-auto w-fit font-mono">
                                                {i.balance_after}{" "}
                                                <span
                                                    className={
                                                        i.amount < 0
                                                            ? "text-red-400"
                                                            : "text-green-400"
                                                    }
                                                >
                                                    (
                                                    {i.amount > 0 &&
                                                        "+"}
                                                    {i.amount})
                                                </span>
                                            </p>
                                        </div>
                                    </div>
                                );
                            })
                        ) : (
                            <div className="py-4 text-center text-[#557797]">
                                暫無點數記錄
                            </div>
                        )}
                    </div>
                </div>

                <div className="mx-auto max-w-2xl rounded-lg border border-[#294565] bg-[#1A325F] p-6">
                    <h3 className="mb-4 text-lg font-semibold text-[#92cbf4]">
                        股票購買紀錄
                    </h3>

                    {/* 取消訂單的通知訊息 */}
                    {cancelSuccess && (
                        <div className="mb-4 rounded-lg border border-green-500/30 bg-green-600/20 p-3">
                            <p className="text-sm text-green-400">
                                ✅ {cancelSuccess}
                            </p>
                        </div>
                    )}
                    {cancelError && (
                        <div className="mb-4 rounded-lg border border-red-500/30 bg-red-600/20 p-3">
                            <p className="text-sm text-red-400">
                                ❌ {cancelError}
                            </p>
                        </div>
                    )}

                    <div className="grid grid-flow-row gap-4">
                        {orderHistory && orderHistory.length > 0 ? (
                            orderHistory.map((i) => {
                                const isCancellable =
                                    canCancelOrder(i);
                                const orderId =
                                    i._id ||
                                    i.id ||
                                    i.order_id ||
                                    i.orderId ||
                                    i["$oid"];
                                const isCancelling =
                                    cancelingOrders.has(orderId);

                                return (
                                    <div
                                        className="rounded-lg border border-[#294565] bg-[#0f203e] p-4"
                                        key={orderId || i.created_at}
                                    >
                                        {/* 訂單基本資訊 */}
                                        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                                            <p className="font-mono text-sm text-[#92cbf4]">
                                                {dayjs(i.created_at)
                                                    .add(8, "hour")
                                                    .format(
                                                        "MM/DD HH:mm",
                                                    )}
                                            </p>
                                            <div className="flex items-center gap-2">
                                                <span
                                                    className={twMerge(
                                                        "rounded px-2 py-1 text-xs font-semibold",
                                                        i.side ===
                                                            "sell"
                                                            ? "bg-green-600/20 text-green-400"
                                                            : "bg-red-600/20 text-red-400",
                                                    )}
                                                >
                                                    {i.side === "sell"
                                                        ? "賣出"
                                                        : "買入"}
                                                </span>
                                                <span className="rounded bg-[#294565] px-2 py-1 text-xs text-[#92cbf4]">
                                                    {i.order_type ===
                                                        "market"
                                                        ? "市價單"
                                                        : "限價單"}
                                                </span>
                                            </div>
                                        </div>

                                        {/* Debug訊息 - 可以在生產環境中移除 */}
                                        {process.env.NODE_ENV ===
                                            "development" && (
                                                <div className="mb-2 rounded bg-gray-800 p-2 text-xs">
                                                    <details>
                                                        <summary className="cursor-pointer text-gray-400">
                                                            Debug：訂單物件結構
                                                        </summary>
                                                        <pre className="mt-1 overflow-auto text-gray-300">
                                                            {JSON.stringify(
                                                                i,
                                                                null,
                                                                2,
                                                            )}
                                                        </pre>
                                                    </details>
                                                </div>
                                            )}

                                        {/* 訂單狀態和詳情 */}
                                        <div className="mb-3">
                                            <p className="font-bold text-[#92cbf4]">
                                                {i.status === "filled"
                                                    ? `✅ 已成交${i.price ? ` → ${i.price}元` : ""}`
                                                    : i.status ===
                                                        "cancelled"
                                                        ? "❌ 已取消"
                                                        : i.status ===
                                                            "pending_limit"
                                                            ? "⏳ 等待中 (限制)"
                                                            : i.status ===
                                                                "partial" ||
                                                                i.status ===
                                                                "pending"
                                                                ? i.filled_quantity >
                                                                    0
                                                                    ? `🔄 部分成交 (${i.filled_quantity}/${i.quantity} 股已成交@${i.filled_price ?? i.price}元，剩餘${i.quantity - i.filled_quantity}股等待)`
                                                                    : "⏳ 等待成交"
                                                                : i.status}
                                            </p>

                                            {/* 訂單詳情 */}
                                            <div className="mt-2 grid grid-cols-2 gap-4 text-sm text-[#557797] md:grid-cols-3">
                                                <div>
                                                    <span>
                                                        數量：
                                                    </span>
                                                    <span className="text-white">
                                                        {i.quantity}{" "}
                                                        股
                                                    </span>
                                                </div>
                                                {i.price && (
                                                    <div>
                                                        <span>
                                                            價格：
                                                        </span>
                                                        <span className="text-white">
                                                            {i.price}{" "}
                                                            元
                                                        </span>
                                                    </div>
                                                )}
                                                {i.filled_quantity >
                                                    0 && (
                                                        <div>
                                                            <span>
                                                                已成交：
                                                            </span>
                                                            <span className="text-green-400">
                                                                {
                                                                    i.filled_quantity
                                                                }{" "}
                                                                股
                                                            </span>
                                                        </div>
                                                    )}
                                            </div>
                                        </div>

                                        {/* 取消按鈕 */}
                                        {isCancellable && (
                                            <div className="flex justify-end">
                                                <button
                                                    onClick={() =>
                                                        openCancelModal(
                                                            i,
                                                            i.order_type,
                                                            i.quantity -
                                                            (i.filled_quantity ||
                                                                0),
                                                        )
                                                    }
                                                    disabled={
                                                        isCancelling
                                                    }
                                                    className={twMerge(
                                                        "rounded-lg px-3 py-1 text-sm font-medium transition-colors",
                                                        isCancelling
                                                            ? "cursor-not-allowed bg-gray-600/50 text-gray-400"
                                                            : "border border-red-500/30 bg-red-600/20 text-red-400 hover:bg-red-600/30",
                                                    )}
                                                >
                                                    {isCancelling
                                                        ? "取消中..."
                                                        : "取消訂單"}
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                );
                            })
                        ) : (
                            <div className="py-4 text-center text-[#557797]">
                                暫無股票交易記錄
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* 取消訂單確認 Modal */}
            <Modal
                isOpen={showCancelModal}
                onClose={closeCancelModal}
                title="確認取消訂單"
                size="md"
            >
                {pendingCancelOrder && (
                    <div className="space-y-4">
                        <div className="rounded-lg border border-orange-500/30 bg-orange-600/10 p-4">
                            <div className="flex items-center gap-2 mb-3">
                                <h3 className="text-lg font-semibold text-orange-400">
                                    你確定要取消這張訂單？
                                </h3>
                            </div>

                            <div className="space-y-2 text-sm text-[#92cbf4]">
                                <div className="flex justify-between">
                                    <span>訂單類型：</span>
                                    <span className="text-white">
                                        {pendingCancelOrder.orderType === "market" ? "市價單" : "限價單"}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span>數量：</span>
                                    <span className="text-white">
                                        {pendingCancelOrder.quantity} 股
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span>訂單 ID：</span>
                                    <span className="font-mono text-white text-xs">
                                        {pendingCancelOrder.orderId}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <p className="text-sm text-[#557797]">
                            謹慎操作，按錯不能幫你復原喔
                        </p>

                        <div className="flex gap-3 pt-2">
                            <button
                                onClick={closeCancelModal}
                                className="flex-1 rounded-lg border border-[#294565] bg-[#1A325F] px-4 py-2 text-[#92cbf4] transition-colors hover:bg-[#294565]"
                            >
                                保留訂單
                            </button>
                            <button
                                onClick={confirmCancelOrder}
                                className="flex-1 rounded-lg bg-red-600 px-4 py-2 text-white transition-colors hover:bg-red-700"
                            >
                                確認取消
                            </button>
                        </div>
                    </div>
                )}
            </Modal>
        </div>
    );
}
