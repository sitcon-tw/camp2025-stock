"use client";

import {
    getWebPointHistory,
    getWebPortfolio,
    getWebStockOrders,
} from "@/lib/api";
import dayjs from "dayjs";
import { LogOut } from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

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
    const router = useRouter();

    // 登出功能
    const handleLogout = () => {
        localStorage.removeItem("isUser");
        localStorage.removeItem("userToken");
        localStorage.removeItem("userData");
        router.push("/");
    };

    // 檢查登入狀態並載入使用者資料
    useEffect(() => {
        const checkAuthAndLoadData = async () => {
            // 檢查必要的認證資料
            const isUser = localStorage.getItem("isUser");
            const token = localStorage.getItem("userToken");
            const telegramData = localStorage.getItem("telegramData");

            console.log("認證檢查:", { isUser, hasToken: !!token, hasTelegramData: !!telegramData });

            // 如果缺少任何必要的認證資料，重新導向到登入頁
            if (!isUser || !token || !telegramData) {
                console.log("缺少認證資料，重新導向到登入頁");
                handleLogout(); // 清理可能不完整的資料
                return;
            }

            // 檢查 token 格式是否正確
            try {
                const tokenParts = token.split('.');
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
                const parsedTelegramData = JSON.parse(telegramData);
                setAuthData(parsedTelegramData);

                console.log("開始載入使用者資料...");
                
                // 載入使用者資料
                const [portfolio, points, stocks] = await Promise.all([
                    getWebPortfolio(token),
                    getWebPointHistory(token),
                    getWebStockOrders(token),
                ]);

                console.log("資料載入成功:", { portfolio, pointsCount: points.length, stocksCount: stocks.length });

                setUser(portfolio);
                setPointHistory(points);
                setOrderHistory(stocks);
                setIsLoading(false);
            } catch (error) {
                console.error("載入使用者資料失敗:", error);
                
                // 處理不同類型的錯誤
                if (error.status === 401 || error.status === 403) {
                    console.log("認證失敗，重新登入");
                    handleLogout();
                } else if (error.status === 404) {
                    console.log("使用者未註冊或資料不存在");
                    setError("使用者帳號未完成註冊，請先完成註冊流程");
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
                <div className="text-center max-w-md p-6">
                    <div className="mb-4 text-6xl">⚠️</div>
                    <h2 className="mb-4 text-xl font-bold text-red-400">載入失敗</h2>
                    <p className="mb-6 text-[#92cbf4]">{error}</p>
                    <div className="space-y-3">
                        <button
                            onClick={() => window.location.reload()}
                            className="w-full rounded-lg bg-[#469FD2] px-4 py-2 text-white hover:bg-[#357AB8] transition-colors"
                        >
                            重新載入
                        </button>
                        <button
                            onClick={handleLogout}
                            className="w-full rounded-lg border border-[#294565] px-4 py-2 text-[#92cbf4] hover:bg-[#1A325F] transition-colors"
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
                    {authData.photo_url ? (
                        <Image
                            src={authData.photo_url}
                            alt="Telegram 頭貼"
                            width={80}
                            height={80}
                            className="h-20 w-20 rounded-full"
                        />
                    ) : (
                        <div className="inline-flex h-20 w-20 items-center justify-center rounded-full bg-[#264173] text-xl font-bold text-[#92cbf4]">
                            {user.username
                                .substring(0, 1)
                                .toUpperCase()}
                        </div>
                    )}
                    <div>
                        <p className="mb-2 text-xl">
                            早安，
                            <b>{user.username}</b>
                        </p>
                        <p className="mb-1 text-[#92cbf4]">
                            你現在擁有的總資產約{" "}
                            <span className="text-white">
                                {user.totalValue?.toLocaleString()}
                            </span>{" "}
                            點
                        </p>
                        <p className="text-sm text-[#92cbf4]">
                            可動用點數共{" "}
                            <span className="text-white">
                                {user.points?.toLocaleString()}
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
                                {user.points?.toLocaleString()}
                            </p>
                        </div>
                        <div>
                            <p className="mb-1 text-center text-sm text-[#557797]">
                                股票數量
                            </p>
                            <p className="text-center text-xl font-bold text-white">
                                {user.stocks?.toLocaleString()}
                            </p>
                        </div>
                        <div>
                            <p className="mb-1 text-center text-sm text-[#557797]">
                                股票價值
                            </p>
                            <p className="text-center text-xl font-bold text-white">
                                {user.stockValue?.toLocaleString()}
                            </p>
                        </div>
                        <div>
                            <p className="mb-1 text-center text-sm text-[#557797]">
                                總資產
                            </p>
                            <p className="text-center text-xl font-bold text-[#92cbf4]">
                                {user.totalValue?.toLocaleString()}
                            </p>
                        </div>
                    </div>
                    {user.avgCost !== undefined && (
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
                                // 延遲隱藏建議，讓點擊事件能夠觸發
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
                                                    e.preventDefault(); // 防止blur事件影響點擊
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
                        {pointHistory.map((i) => {
                            return (
                                <div
                                    className="grid grid-cols-5 space-x-4"
                                    key={i.created_at}
                                >
                                    <p className="font-mono">
                                        {dayjs(i.created_at).format(
                                            "MM/DD HH:mm",
                                        )}
                                    </p>
                                    <p className="col-span-3 text-[#92cbf4]">
                                        {i.note}
                                    </p>

                                    <p className="ml-auto font-mono">
                                        {i.balance_after}{" "}
                                        <span
                                            className={
                                                i.amount < 0
                                                    ? "text-red-400"
                                                    : "text-green-400"
                                            }
                                        >
                                            ({i.amount > 0 && "+"}
                                            {i.amount})
                                        </span>
                                    </p>
                                </div>
                            );
                        })}
                    </div>
                </div>

                <div className="mx-auto max-w-2xl rounded-lg border border-[#294565] bg-[#1A325F] p-6">
                    <h3 className="mb-4 text-lg font-semibold text-[#92cbf4]">
                        股票購買紀錄
                    </h3>

                    <div className="grid grid-flow-row gap-4">
                        {orderHistory.map((i) => {
                            return (
                                <div
                                    className="grid grid-cols-5 space-x-4"
                                    key={i.created_at}
                                >
                                    <p className="font-mono">
                                        {dayjs(i.created_at).format(
                                            "MM/DD HH:mm",
                                        )}
                                    </p>
                                    <p className="col-span-3 text-[#92cbf4]">
                                        {i.status === "filled"
                                            ? `✅ 已成交${i.price ? ` → ${i.price}元` : ""}`
                                            : i.status === "cancelled"
                                                ? "❌ 已取消"
                                                : i.status ===
                                                    "pending_limit"
                                                    ? "等待中 (限制)"
                                                    : i.status ===
                                                        "partial" ||
                                                        i.status ===
                                                        "pending"
                                                        ? i.filled_quantity >
                                                            0
                                                            ? `部分成交 (${i.filled_quantity}/${i.quantity} 股已成交@${i.filled_price ?? i.price}元，剩餘${i.quantity - i.filled_quantity}股等待)`
                                                            : "等待成交"
                                                        : i.status}
                                    </p>

                                    <p className="ml-auto">
                                        {i.side === "sell"
                                            ? "賣出"
                                            : "買入"}
                                    </p>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
}
