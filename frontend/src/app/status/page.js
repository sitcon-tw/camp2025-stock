"use client";

import HeaderBar from "@/components/HeaderBar";
import StockChart from "@/components/StockChart";
import TradingTabs from "@/components/TradingTabs";
import { apiService } from "@/services/apiService";
import { useEffect, useState } from "react";
import { twMerge } from "tailwind-merge";

export default function Status() {
    const [stockData, setStockData] = useState({
        lastPrice: 0,
        change: 0,
        changePercent: 0,
        high: 0,
        low: 0,
        open: 0,
        volume: 0,
    });

    const [tradingStats, setTradingStats] = useState({
        total_trades: 0,
        total_volume: 0,
        total_amount: 0,
    });

    const [error, setError] = useState(null);
    const [showTradeModal, setShowTradeModal] = useState(false);
    const [tradeType, setTradeType] = useState("buy"); // "buy" or "sell"
    const [isMarketPrice, setIsMarketPrice] = useState(true);
    const [customPrice, setCustomPrice] = useState("");
    const [isModalClosing, setIsModalClosing] = useState(false);

    const fetchData = async () => {
        try {
            const [priceData, statsData] = await Promise.all([
                apiService.getPriceData(),
                apiService.getTradingStatsData(),
            ]);
            setStockData(priceData);
            setTradingStats(statsData);
            setError(null);
        } catch (err) {
            console.error("獲取資料失敗:", err);
            setError("無法獲取資料");
        }
    };
    useEffect(() => {
        let isMounted = true;

        const fetchInitialData = async () => {
            if (isMounted) {
                await fetchData();
            }
        };

        fetchInitialData();

        return () => {
            isMounted = false;
        };
    }, []);

    const currentPrice = stockData.lastPrice;
    const changePercent = parseFloat(stockData.changePercent) || 0;

    const handleCloseTradeModal = () => {
        setIsModalClosing(true);
        setTimeout(() => {
            setShowTradeModal(false);
            setIsModalClosing(false);
        }, 200); // Match animation duration
    };

    return (
        <div className="min-h-screen w-full bg-[#0f203e] pb-28 md:pb-0">
            <div className="flex w-full max-w-none flex-col px-4 lg:px-8">
                <HeaderBar />

                {/* 錯誤狀態 */}
                {error && (
                    <div className="mt-8 rounded-lg border border-red-600 bg-red-900/30 p-4">
                        <div className="text-sm text-red-400">
                            {error}
                        </div>
                    </div>
                )}

                {/* 響應式布局：手機版垂直，桌面版左右分欄 */}
                <div className="flex flex-col lg:h-[calc(100vh-12rem)] lg:flex-row lg:gap-8 xl:gap-12">
                    {/* 左半邊：圖表 + 價格資訊 */}
                    <div className="flex w-full flex-col lg:w-3/5 xl:w-2/3">
                        {/* 股市趨勢圖 */}
                        <div className="mt-3 mb-2 min-h-0 w-full flex-1">
                            <StockChart
                                currentPrice={currentPrice}
                                changePercent={changePercent}
                            />
                        </div>

                        {/* 買賣按鈕 */}
                        <div className="mb-4 grid grid-cols-2 gap-2 text-center">
                            <button
                                onClick={() => {
                                    setTradeType("buy");
                                    setShowTradeModal(true);
                                }}
                                className="rounded-lg bg-[#1B325E] hover:bg-[#2A4A7F] p-3 xl:p-4 transition-colors"
                            >
                                <p className="text-lg font-bold lg:text-2xl xl:text-3xl text-white">
                                    買
                                </p>
                            </button>
                            <button
                                onClick={() => {
                                    setTradeType("sell");
                                    setShowTradeModal(true);
                                }}
                                className="rounded-lg bg-[#1B325E] hover:bg-[#2A4A7F] p-3 xl:p-4 transition-colors"
                            >
                                <p className="text-lg font-bold lg:text-2xl xl:text-3xl text-white">
                                    賣
                                </p>
                            </button>
                        </div>

                        {/* 價格資訊 */}
                        <div className="mb-4 flex-shrink-0">
                            <div className="grid grid-cols-2 gap-2 text-center lg:grid-cols-3 lg:gap-4 xl:grid-cols-6 xl:gap-6">
                                <div className="rounded-lg bg-[#1A325F] p-3 xl:p-4">
                                    <h5 className="text-xs text-white lg:text-sm xl:text-base">
                                        開盤價
                                    </h5>
                                    <p className="text-lg font-bold lg:text-2xl xl:text-3xl">
                                        {Math.round(stockData.open)}
                                    </p>
                                    <p className="text-xs text-white lg:text-sm xl:text-base">
                                        點
                                    </p>
                                </div>
                                <div className="rounded-lg bg-[#1A325F] p-3 xl:p-4">
                                    <h5 className="text-xs text-white lg:text-sm xl:text-base">
                                        今日最低
                                    </h5>
                                    <p className="text-lg font-bold lg:text-2xl xl:text-3xl">
                                        {Math.round(stockData.low)}
                                    </p>
                                    <p className="text-xs text-white lg:text-sm xl:text-base">
                                        點
                                    </p>
                                </div>
                                <div className="rounded-lg bg-[#1A325F] p-3 xl:p-4">
                                    <h5 className="text-xs text-white lg:text-sm xl:text-base">
                                        今日最高
                                    </h5>
                                    <p className="text-lg font-bold lg:text-2xl xl:text-3xl">
                                        {Math.round(stockData.high)}
                                    </p>
                                    <p className="text-xs text-white lg:text-sm xl:text-base">
                                        點
                                    </p>
                                </div>
                                <div className="rounded-lg bg-[#1A325F] p-3 xl:p-4">
                                    <h5 className="text-xs text-white lg:text-sm xl:text-base">
                                        今日成交量
                                    </h5>
                                    <p className="text-lg font-bold lg:text-2xl xl:text-3xl">
                                        {tradingStats.total_volume.toLocaleString()}
                                    </p>
                                    <p className="text-xs text-white lg:text-sm xl:text-base">
                                        股
                                    </p>
                                </div>
                                <div className="rounded-lg bg-[#1A325F] p-3 xl:p-4">
                                    <h5 className="text-xs text-white lg:text-sm xl:text-base">
                                        成交額
                                    </h5>
                                    <p className="text-lg font-bold lg:text-2xl xl:text-3xl">
                                        {tradingStats.total_amount.toLocaleString()}
                                    </p>
                                    <p className="text-xs text-white lg:text-sm xl:text-base">
                                        點
                                    </p>
                                </div>
                                <div className="rounded-lg bg-[#1A325F] p-3 xl:p-4">
                                    <h5 className="text-xs text-white lg:text-sm xl:text-base">
                                        成交筆數
                                    </h5>
                                    <p className="text-lg font-bold lg:text-2xl xl:text-3xl">
                                        {tradingStats.total_trades.toLocaleString()}
                                    </p>
                                    <p className="text-xs text-white lg:text-sm xl:text-base">
                                        筆
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* 右半邊：五檔報價 + 交易紀錄 (桌面版專用) */}
                    <div className="hidden w-full lg:flex lg:w-2/5 lg:flex-col xl:w-1/3">
                        {/* 五檔報價 */}
                        <div className="mt-3 mb-4 flex-shrink-0">
                            <TradingTabs
                                activeTab="orderbook"
                                currentPrice={currentPrice}
                            />
                        </div>

                        {/* 交易紀錄 */}
                        <div className="flex min-h-0 flex-1 flex-col">
                            <TradingTabs
                                activeTab="history"
                                currentPrice={currentPrice}
                            />
                        </div>
                    </div>
                </div>

                {/* 手機版的切換式 TAB */}
                <div className="mt-3 lg:hidden">
                    <TradingTabs currentPrice={currentPrice} />
                </div>
            </div>

            {/* 交易 Modal */}
            {showTradeModal && (
                <div
                    className={twMerge(
                        "fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm",
                        isModalClosing
                            ? "animate-modal-close-bg"
                            : "animate-modal-open-bg",
                    )}
                    onClick={handleCloseTradeModal}
                >
                    <div
                        className={twMerge(
                            "w-full max-w-md rounded-xl bg-[#1A325F] p-6 shadow-2xl",
                            isModalClosing
                                ? "animate-modal-close"
                                : "animate-modal-open",
                        )}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="mb-4 flex items-center justify-between">
                            <h2 className="text-xl font-bold text-[#AFE1F5]">
                                {tradeType === "buy" ? "買入" : "賣出"}
                            </h2>
                            <button
                                onClick={handleCloseTradeModal}
                                className="text-xl font-bold text-[#AFE1F5] hover:text-[#7BC2E6]"
                            >
                                ×
                            </button>
                        </div>

                        <div className="space-y-4">
                            {/* 市價選項 */}
                            <div className="flex items-center space-x-3">
                                <input
                                    type="checkbox"
                                    id="marketPrice"
                                    checked={isMarketPrice}
                                    onChange={(e) => setIsMarketPrice(e.target.checked)}
                                    className="h-4 w-4 rounded border-[#4f6f97] bg-[#0f203e] text-[#7BC2E6] focus:ring-[#7BC2E6]"
                                />
                                <label htmlFor="marketPrice" className="text-[#AFE1F5]">
                                    市價 ({Math.round(currentPrice)})
                                </label>
                            </div>

                            {/* 價格輸入 */}
                            <div>
                                <label className="block text-sm font-medium text-[#AFE1F5] mb-2">
                                    價格
                                </label>
                                <input
                                    type="number"
                                    value={isMarketPrice ? Math.round(currentPrice) : customPrice}
                                    onChange={(e) => setCustomPrice(e.target.value)}
                                    disabled={isMarketPrice}
                                    placeholder="請輸入價格"
                                    className="w-full rounded-lg border border-[#4f6f97] bg-[#0f203e] px-3 py-2 text-[#AFE1F5] placeholder-gray-400 focus:border-[#7BC2E6] focus:outline-none focus:ring-1 focus:ring-[#7BC2E6] disabled:bg-gray-700 disabled:text-gray-400"
                                />
                            </div>

                            {/* 數量輸入 */}
                            <div>
                                <label className="block text-sm font-medium text-[#AFE1F5] mb-2">
                                    數量
                                </label>
                                <input
                                    type="number"
                                    placeholder="請輸入數量"
                                    className="w-full rounded-lg border border-[#4f6f97] bg-[#0f203e] px-3 py-2 text-[#AFE1F5] placeholder-gray-400 focus:border-[#7BC2E6] focus:outline-none focus:ring-1 focus:ring-[#7BC2E6]"
                                />
                            </div>

                            {/* 按鈕 */}
                            <div className="flex gap-3 pt-4">
                                <button
                                    onClick={handleCloseTradeModal}
                                    className="flex-1 rounded-lg border border-[#4f6f97] bg-transparent px-4 py-2 text-[#AFE1F5] hover:bg-[#4f6f97]/20"
                                >
                                    取消
                                </button>
                                <button
                                    className="flex-1 rounded-lg px-4 py-2 text-black font-medium bg-[#7CBEE4] hover:bg-[#6AADD1]"
                                >
                                    確認{tradeType === "buy" ? "買入" : "賣出"}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <style jsx global>{`
                @keyframes modal-open {
                    from {
                        opacity: 0;
                        transform: scale(0.95);
                    }
                    to {
                        opacity: 1;
                        transform: scale(1);
                    }
                }

                @keyframes modal-close {
                    from {
                        opacity: 1;
                        transform: scale(1);
                    }
                    to {
                        opacity: 0;
                        transform: scale(0.95);
                    }
                }

                @keyframes modal-open-bg {
                    from {
                        opacity: 0;
                        backdrop-filter: blur(0px);
                    }
                    to {
                        opacity: 1;
                        backdrop-filter: blur(4px);
                    }
                }

                @keyframes modal-close-bg {
                    from {
                        opacity: 1;
                        backdrop-filter: blur(4px);
                    }
                    to {
                        opacity: 0;
                        backdrop-filter: blur(0px);
                    }
                }

                .animate-modal-open {
                    animation: modal-open 0.2s ease-out;
                }

                .animate-modal-close {
                    animation: modal-close 0.2s ease-in;
                }

                .animate-modal-open-bg {
                    animation: modal-open-bg 0.2s ease-out;
                }

                .animate-modal-close-bg {
                    animation: modal-close-bg 0.2s ease-in;
                }
            `}</style>
        </div>
    );
}
