"use client";

import { getWebPortfolio, placeWebStockOrder } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function Dashboard() {
    const [isLoading, setIsLoading] = useState(true);
    const [user, setUser] = useState(null);
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
            const isUser = localStorage.getItem("isUser");
            const token = localStorage.getItem("userToken");

            if (!isUser || !token) {
                router.push("/telegram-login");
                return;
            }

            try {
                // 載入使用者資料
                const portfolio = await getWebPortfolio(token);

                setUser(portfolio);
                setIsLoading(false);
            } catch (error) {
                console.error("載入使用者資料失敗:", error);
                if (error.status === 401) {
                    // Token 過期，重新登入
                    handleLogout();
                } else {
                    setError("載入資料失敗，請重新整理頁面");
                    setIsLoading(false);
                }
            }
        };

        checkAuthAndLoadData();
    }, [router]);

    // Portfolio 組件
    const PortfolioView = () => {
        if (!user) return <div>載入中...</div>;

        return (
            <div className="space-y-6">
                {/* 資產總覽 */}
                <div className="rounded-lg border border-[#294565] bg-[#1a3a5c] p-6">
                    <h3 className="mb-4 text-lg font-semibold text-[#92cbf4]">
                        資產總覽
                    </h3>
                    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                        <div>
                            <p className="text-sm text-[#557797]">
                                現金點數
                            </p>
                            <p className="text-xl font-bold text-white">
                                {user.points?.toLocaleString()}
                            </p>
                        </div>
                        <div>
                            <p className="text-sm text-[#557797]">
                                股票數量
                            </p>
                            <p className="text-xl font-bold text-white">
                                {user.stocks?.toLocaleString()}
                            </p>
                        </div>
                        <div>
                            <p className="text-sm text-[#557797]">
                                股票價值
                            </p>
                            <p className="text-xl font-bold text-white">
                                {user.stockValue?.toLocaleString()}
                            </p>
                        </div>
                        <div>
                            <p className="text-sm text-[#557797]">
                                總資產
                            </p>
                            <p className="text-xl font-bold text-[#92cbf4]">
                                {user.totalValue?.toLocaleString()}
                            </p>
                        </div>
                    </div>
                    {user.avgCost !== undefined && (
                        <div className="mt-4 border-t border-[#294565] pt-4">
                            <p className="text-sm text-[#557797]">
                                平均成本:{" "}
                                <span className="font-semibold text-white">
                                    {user.avgCost}
                                </span>
                            </p>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    // 交易組件
    const TradingView = () => {
        const [orderType, setOrderType] = useState("market");
        const [side, setSide] = useState("buy");
        const [quantity, setQuantity] = useState("");
        const [price, setPrice] = useState("");
        const [isSubmitting, setIsSubmitting] = useState(false);

        const handleSubmitOrder = async (e) => {
            e.preventDefault();
            setIsSubmitting(true);
            setError("");

            try {
                const token = localStorage.getItem("userToken");
                const orderData = {
                    order_type: orderType,
                    side: side,
                    quantity: parseInt(quantity),
                    ...(orderType === "limit" && {
                        price: parseInt(price),
                    }),
                };

                await placeWebStockOrder(token, orderData);

                // 重新載入投資組合
                const portfolioData = await getWebPortfolio(token);
                setPortfolio(portfolioData);

                // 清空表單
                setQuantity("");
                setPrice("");

                alert("下單成功！");
            } catch (error) {
                console.error("下單失敗:", error);
                setError(error.message || "下單失敗");
            } finally {
                setIsSubmitting(false);
            }
        };

        return (
            <div className="rounded-lg border border-[#294565] bg-[#1a3a5c] p-6">
                <h3 className="mb-4 text-lg font-semibold text-[#92cbf4]">
                    股票交易
                </h3>

                <form
                    onSubmit={handleSubmitOrder}
                    className="space-y-4"
                >
                    {/* 買賣方向 */}
                    <div>
                        <label className="mb-2 block text-sm font-medium text-[#557797]">
                            買賣方向
                        </label>
                        <div className="grid grid-cols-2 gap-2">
                            <button
                                type="button"
                                onClick={() => setSide("buy")}
                                className={`rounded-lg px-4 py-2 font-medium transition-colors ${
                                    side === "buy"
                                        ? "bg-green-600 text-white"
                                        : "bg-[#294565] text-[#557797] hover:bg-[#3a5678]"
                                }`}
                            >
                                買入
                            </button>
                            <button
                                type="button"
                                onClick={() => setSide("sell")}
                                className={`rounded-lg px-4 py-2 font-medium transition-colors ${
                                    side === "sell"
                                        ? "bg-red-600 text-white"
                                        : "bg-[#294565] text-[#557797] hover:bg-[#3a5678]"
                                }`}
                            >
                                賣出
                            </button>
                        </div>
                    </div>

                    {/* 訂單類型 */}
                    <div>
                        <label className="mb-2 block text-sm font-medium text-[#557797]">
                            訂單類型
                        </label>
                        <select
                            value={orderType}
                            onChange={(e) =>
                                setOrderType(e.target.value)
                            }
                            className="w-full rounded-lg border-2 border-[#294565] bg-transparent px-4 py-2 text-white focus:border-cyan-400 focus:outline-none"
                        >
                            <option
                                value="market"
                                className="bg-[#1a3a5c]"
                            >
                                市價單
                            </option>
                            <option
                                value="limit"
                                className="bg-[#1a3a5c]"
                            >
                                限價單
                            </option>
                        </select>
                    </div>

                    {/* 數量 */}
                    <div>
                        <label className="mb-2 block text-sm font-medium text-[#557797]">
                            數量
                        </label>
                        <input
                            type="number"
                            value={quantity}
                            onChange={(e) =>
                                setQuantity(e.target.value)
                            }
                            min="1"
                            required
                            className="w-full rounded-lg border-2 border-[#294565] bg-transparent px-4 py-2 text-white placeholder-slate-400 focus:border-cyan-400 focus:outline-none"
                            placeholder="輸入股票數量"
                        />
                    </div>

                    {/* 價格（限價單才顯示） */}
                    {orderType === "limit" && (
                        <div>
                            <label className="mb-2 block text-sm font-medium text-[#557797]">
                                價格
                            </label>
                            <input
                                type="number"
                                value={price}
                                onChange={(e) =>
                                    setPrice(e.target.value)
                                }
                                min="1"
                                required
                                className="w-full rounded-lg border-2 border-[#294565] bg-transparent px-4 py-2 text-white placeholder-slate-400 focus:border-cyan-400 focus:outline-none"
                                placeholder="輸入限價"
                            />
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={isSubmitting}
                        className="w-full rounded-xl bg-[#81c0e7] py-3 font-bold text-[#092e58] transition-colors duration-200 hover:bg-[#70b3d9] disabled:cursor-not-allowed disabled:bg-gray-500"
                    >
                        {isSubmitting ? "下單中..." : "確認下單"}
                    </button>
                </form>
            </div>
        );
    };

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

    return (
        <div className="min-h-screen bg-[#0f203e] pb-20">
            {/* 標題列 */}
            <div className="border-b border-[#294565] bg-[#1a3a5c] px-4 py-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-xl font-bold text-[#92cbf4]">
                            投資儀表板
                        </h1>
                        {user && (
                            <p className="text-sm text-[#557797]">
                                歡迎，{user.name || user.id}
                            </p>
                        )}
                    </div>
                    <button
                        onClick={handleLogout}
                        className="text-sm text-[#557797] transition-colors hover:text-red-400"
                    >
                        登出
                    </button>
                </div>
            </div>

            {/* 頁籤導航 */}
            <div className="border-b border-[#294565] bg-[#1a3a5c]">
                <div className="flex">
                    <button
                        onClick={() => setActiveTab("portfolio")}
                        className={`flex-1 py-3 text-sm font-medium transition-colors ${
                            activeTab === "portfolio"
                                ? "border-b-2 border-[#92cbf4] text-[#92cbf4]"
                                : "text-[#557797] hover:text-[#92cbf4]"
                        }`}
                    >
                        投資組合
                    </button>
                    <button
                        onClick={() => setActiveTab("trading")}
                        className={`flex-1 py-3 text-sm font-medium transition-colors ${
                            activeTab === "trading"
                                ? "border-b-2 border-[#92cbf4] text-[#92cbf4]"
                                : "text-[#557797] hover:text-[#92cbf4]"
                        }`}
                    >
                        股票交易
                    </button>
                </div>
            </div>

            {/* 內容區域 */}
            <div className="p-4">
                {error && (
                    <div className="mb-4 rounded-lg border border-red-500/30 bg-red-900/20 p-3 text-center text-sm text-red-400">
                        {error}
                    </div>
                )}

                {activeTab === "portfolio" && <PortfolioView />}
                {activeTab === "trading" && <TradingView />}
            </div>
        </div>
    );
}
